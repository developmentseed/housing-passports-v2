"""
Package prediction results into a PostGRES database for better organization

PostGRES DB will have 3 tables:
    1. Prediction (each bbox identified)
    2. Image (each image captured during data collection)
    3. Building (PostGIS geometry and list of predictions)
"""
import csv
import json
import os.path as op

import click
import numpy as np
import tensorflow as tf
from geoalchemy2.functions import ST_Intersects, ST_Within
# from object_detection.utils import label_map_util
from osgeo import ogr
from sqlalchemy import create_engine, text, and_,join ,outerjoin
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from housing_passports.db_classes import Image, Building, Detection, Base
from housing_passports.utils_transforms import (get_LR_visual_extents, interpolate, generate_ray, generate_buffer_ray)
from housing_passports.utils_convert import (create_category_index_from_labelmap)

### script used to writen by TF1.0
### adding following lines to make it compatible with TF2.0
# label_map_util.tf = tf.compat.v1
# tf.gfile = tf.io.gfile


def add_buildings(geomfile_fpath, session):
    """Add a building polygon to the database

    Parameters
    ----------
    geomfile_fpath: str
        File path to shapefile containing building polygons
        Note: 
            The shapefile should have the column "neighborho" which refers to neighborhood 
    session: sqlalchemy.orm.session.Session
        SQL Alchemy session handle to the database

    Returns
    -------
    n_rows_added: int
        Number of images added to the session
    """

    # Get driver for OGR loading
    ogr_driver = 'GeoJSON'
    if op.splitext(geomfile_fpath)[1] == '.shp':
        ogr_driver = 'ESRI Shapefile'

    driver = ogr.GetDriverByName(ogr_driver)
    dataSource = driver.Open(geomfile_fpath, 0)  # 0 means read-only. 1 means writeable.

    # Check to see if geojson is found.
    if dataSource is None:
        print('Could not open {}'.format(geomfile_fpath))
        return

    layer = dataSource.GetLayer()
    n_rows_added = 0

    # Load all building polygons
    for gi in tqdm(range(layer.GetFeatureCount()),
                   desc='Adding buildings to DB Session'):
        feat = layer.GetFeature(gi)
        geom = feat.GetGeometryRef()

        if geom is None:
            print(f'Geometry for feature {feat} is None. Skipping...')
            continue

        # Dump in database
        if geom.GetGeometryName() == 'POLYGON' and geom.IsValid():
            centroid = geom.Centroid().GetPoint()

            session.add(Building(footprint=geom.ExportToWkt(),
                                 neighborhood=feat.GetField('neighborho'),  # neighborhood, TODO Fix later
                                 lon=centroid[0],
                                 lat=centroid[1],
                                 building_metadata=feat.items(),
                                 centroid=geom.Centroid().ExportToWkt()))
            n_rows_added += 1

    return n_rows_added


def add_images(image_csv_fpath, session):
    """Load image information from CSV file into database

    Parameters
    ----------
    image_csv_fpath: str
        Filepath to the CSV file containing image information
        ================================== CSV format =========================================
        heading[deg],image_fname,frame,latitude[deg],longitude[deg],cam,neighborhood,subfolder
        238.81604587884,ladybug_14062044_20190628_141526_Cube_000000_Cam1_879_090-0881.jpg,ladybug_14062044_20190628_141526_Cube_000000,-0.937739981443431,100.37766844977699,1,padang,PADANG_01
        238.81604587884,ladybug_14062044_20190628_141526_Cube_000000_Cam3_879_090-0881.jpg,ladybug_14062044_20190628_141526_Cube_000000,-0.937739981443431,100.37766844977699,3,padang,PADANG_01
        238.91803236637298,ladybug_14062044_20190628_141526_Cube_000001_Cam1_880_091-3497.jpg,ladybug_14062044_20190628_141526_Cube_000001,-0.93774492395104,100.377660678983,1,padang,PADANG_01
        238.91803236637298,ladybug_14062044_20190628_141526_Cube_000001_Cam3_880_091-3497.jpg,ladybug_14062044_20190628_141526_Cube_000001,-0.93774492395104,100.377660678983,3,padang,PADANG_01
        239.790417905239,ladybug_14062044_20190628_141526_Cube_000003_Cam1_882_093-1096.jpg,ladybug_14062044_20190628_141526_Cube_000003,-0.9377541950399528,100.377645015404,1,padang,PADANG_01
        239.790417905239,ladybug_14062044_20190628_141526_Cube_000003_Cam3_882_093-1096.jpg,ladybug_14062044_20190628_141526_Cube_000003,-0.9377541950399528,100.377645015404,3,padang,PADANG_01
        ========================================================================================
    session: sqlalchemy.orm.session.Session
        SQL Alchemy session handle to the database

    Returns
    -------
    n_rows_added: int
        Number of images added to the session
    """
    n_rows_added = 0

    # Load CSV file containing GPS information
    with open(image_csv_fpath, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        rows = list(reader)
        #  Iterate through all rows adding each image's information to DB

        for row in tqdm(rows, desc=f'Adding images to DB Session...', total=len(rows)):
            # for cam_num in cam_nums:
            try:
                lat = float(row['latitude[deg]'])
                lon = float(row['longitude[deg]'])
                session.add(Image(lat=lat,
                                  lon=lon,
                                  heading=float(row['heading[deg]']),
                                  neighborhood=row['neighborhood'],  # neighborhood
                                  subfolder=row['subfolder'],
                                  frame=row['frame'],
                                  image_fname=row['image_fname'],
                                  cam=int(row['cam'])
                                  ))
                n_rows_added += 1
            except ValueError:
                print("could not convert string to float: ''")
    return n_rows_added


def add_detections(det_group, session, classes_to_include=None):
    # print(det_group)
    """Add a list of detections to database (incl. with link to image).

    Parameters
    ----------
    det_group: list
        List of detections. Likely loaded from ML-produced json files. Each
        item in the list should contain all detections for one image.
    session: sqlalchemy.orm.session.Session
        SQL Alchemy session handle to the database
    classes_to_include: None or str
        If specified, only add detections for these class strings.

    Returns
    -------
    n_rows_added: int
        Number of detections added to the session
    """

    n_rows_added = 0
    missing_img_report = []

    # Iterate through all ML detections
    # TODO: could maybe speed this up using a better query strategy
    for det in tqdm(det_group, desc='Connecting detections to images and adding to session'):
        try:
            with session.begin_nested():
                image = session.query(Image).filter(and_(Image.frame == det['frame'],
                                                         Image.subfolder == det['subfolder'],
                                                         Image.image_fname == det['image_fname'],
                                                         Image.cam == det['cam'])).first()

                if image is None:
                    missing_img_report.append(
                        f'No image found for filters: {det["neighborhood"]}, '
                        f'{det["subfolder"]}, {det["frame"]}, {op.basename(det["image_fname"])}, {det["cam"]}. '
                        'Missing in image information/trajectory file?')
                    continue

                # Get information from matching image
                vext = get_LR_visual_extents(image.heading)

                for score, class_id, class_str, bbox, od_mean_x in zip(
                        det['detection_scores'],
                        det['detection_classes'],
                        det['detection_class_strs'],
                        det['detection_boxes'],
                        det['od_mean_xs']):

                    if classes_to_include and class_str not in classes_to_include:
                        continue

                    if det['cam'] == 1:
                        det_heading = interpolate(od_mean_x, vext['r_min'], vext['r_max'])
                    elif det['cam'] == 3:
                        det_heading = interpolate(od_mean_x, vext['l_min'], vext['l_max'])
                    else:
                        raise RuntimeError('Key indicating camera view unrecognized')

                    wkt_linestring = generate_ray(image.lon, image.lat, det_heading)
                    wkt_buffer = generate_buffer_ray(wkt_linestring)

                    detection = Detection(image_id=image.id,
                                          y_min=bbox[0], x_min=bbox[1],
                                          y_max=bbox[2], x_max=bbox[3],
                                          class_id=class_id,
                                          class_str=class_str,
                                          confidence=score,
                                          neighborhood=image.neighborhood,
                                          angle=det_heading,
                                          detection_ray=wkt_linestring,
                                          ray_buffer=wkt_buffer)

                    session.add(detection)

                n_rows_added += 1

            session.commit()

        except Exception as e:
            print(f"Error processing detection {det}: {e}")
            session.rollback()

    for msg in missing_img_report:
        print(msg)

    return n_rows_added


def _get_session(db_url, use_batch_mode=True, echo=False):
    """Helper to get an SQLAlchemy DB session"""
    # `use_batch_mode` is experimental currently, but needed for `executemany`
    engine = create_engine(db_url, echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        connection = session.connection()
        print('Successfully connected to database.')
    except:
        raise RuntimeError(f'Couldn\'t connect to db: {db_url}')

    return session


def _load_detections(det_data, class_map):
    """Add all detections from one json file
    Format detections,should be like so:
    {
        "neighborhood": "padang",
        "subfolder": "PADANG_30",
        "frame": "ladybug_14062044_20190721_081658_Cube_027495",
        "detection_boxes": [...],
        "detection_classes": [... ],
        "detection_scores": [...],
        "cam": 3,
        "image_fname": "ladybug_14062044_20190721_081658_Cube_027495_Cam3_27778_033-0732.jpg"
    }
    """

    if not det_data['detection_scores']:
        return

    # Identify image from database
    det_data['cam'] = int(str(det_data['cam']))
    det_data['detection_classes'] = [int(class_id)
                                     for class_id in det_data['detection_classes']]
    det_data['detection_class_strs'] = [class_map[int(class_id)]['name']
                                        for class_id in det_data['detection_classes']]
    det_data['od_mean_xs'] = [np.mean([bbox[1], bbox[3]])
                              for bbox in det_data['detection_boxes']]

    return det_data


@click.command(short_help="Populate each building's metadata field using pre-attached detections.")
@click.argument('db-url', nargs=1)
@click.option("--fpath-parts", type=click.Path(exists=True),
              help="JSON file containing a list of building parts under `parts` key.")
@click.option("--fpath-property-groups", type=click.Path(exists=True),
              help="JSON file containing a dictionary of property names and included keys.")
@click.option("--neighborhood", type=str,
              help="Name of neighborhood to store in DB for all detections.")
def distill_building_metadata(db_url, fpath_parts, fpath_property_groups,
                              neighborhood):
    """Helper to distill all building detections into metadata."""

    session = _get_session(db_url)
    query = session.query(Building). \
        filter(Building.neighborhood == neighborhood)

    # Load parts and property information
    if fpath_parts:
        with open(fpath_parts, 'r') as json_file:
            parts_dict = json.load(json_file)
        if not 'parts' in parts_dict.keys():
            raise ValueError('`fpath-parts` must point to json with `parts` key')
        parts_list = parts_dict['parts']

    if fpath_property_groups:
        with open(fpath_property_groups, 'r') as json_file:
            property_groups = json.load(json_file)

    # Iterate over buildings, considlidate metadata
    for building in tqdm(query.yield_per(1000),
                         desc='Distilling detections into building metadata',
                         total=query.count()):

        # Must create new dicts (and not update original ones) when assigning to the metadata
        if fpath_parts:
            all_parts = building.get_consolidated_parts(parts_list)
            all_parts.update(building.building_metadata)
            building.building_metadata = all_parts

        if fpath_property_groups:
            all_props = building.get_consolidated_properties(property_groups)
            all_props.update(building.building_metadata)
            building.building_metadata = all_props

    session.commit()


@click.command(short_help="Dump images, trajectories, buildings, and detections into a database.")
@click.argument('db-url', nargs=1)
@click.option("--trajectory-fpath", type=click.Path(exists=True),
              help="CSV file containing GPS trajectory info for each image")
@click.option("--geomfile-fpath", type=click.Path(exists=True),
              help="Shapefile or geojson containing building footprints")
# @click.option("--neighborhood", type=str,
#               help="Name of neighborhood to store in DB for all detections.")
# @click.option("--neighborhood-dir", type=click.Path(exists=True),
#               help="Neighborhxood directory with subfolders containing ML predictions.")
@click.option("--parts-inference-fpath", type=click.Path(exists=True),
              help="Json file with all containing ML predictions for buuilding parts.")
@click.option("--props-inference-fpath", type=click.Path(exists=True),
              help="Json file with all containing ML predictions for buuilding parts.")
@click.option("--parts-map-fpath", type=click.Path(exists=True),
              help="PBTXT file mapping building parts class IDs to strings")
@click.option("--props-map-fpath", type=click.Path(exists=True),
              help="PBTXT file mapping building properties class IDs to strings")
@click.option('--det_classes', type=str, default=None, multiple=True,
              help='Property classes to include (e.g., "window", "pre_1940").')
def export_to_db(db_url, trajectory_fpath, geomfile_fpath,
                 parts_inference_fpath, props_inference_fpath, parts_map_fpath, props_map_fpath,
                 det_classes):
    """Export housing passport information to a database.

    Parameters
    ----------
    db_url: str
        Database access URL (including username and password if necessary).
    trajectory_fpath: str
        CSV file containing GPS trajectory info for each image
    geomfile_fpath: str
        Shapefile or geojson containing building footprints
    parts_inference_fpath: str
        Json tthat contains ML predictions for parts.
    props_inference_fpath: str
        Json tthat contains ML predictions for properties.
    parts_map_fpath: str
        TF PBTXT file mapping building part class IDs to strings
    props_map_fpath: str
        TF PBTXT file mapping building property class IDs to strings
    det_classes: list or None
        List of class names (e.g., 'complete', 'window', etc.) used to filter
        detections.
    """

    # Create database connection
    session = _get_session(db_url)

    # Load category index
    map_parts = create_category_index_from_labelmap(
        parts_map_fpath, use_display_name=True)
    map_properties = create_category_index_from_labelmap(
        props_map_fpath, use_display_name=True)
    # print(map_parts, map_properties)

    ######################################
    # Add buildings and images to database
    ######################################

    if geomfile_fpath is not None:
        n_buildings = add_buildings(geomfile_fpath, session)
        print(f'Committing {n_buildings} buildings...')
        session.commit()
        print('Done.\n')

    if trajectory_fpath is not None:
        n_images = add_images(trajectory_fpath, session)
        print(f'Committing {n_images} images...')
        session.commit()
        print('Done.\n')

    # # # ######################################
    # # # # Adding the index after the table sv_images is populated 
    # # # # will be faster, more compact and more efficient indexation 
    # # # ######################################

    print('Creating index on buildings table...')
    session.execute(text('CREATE INDEX IF NOT EXISTS idx_building_id ON buildings(id);'))
    session.execute(text('CREATE INDEX IF NOT EXISTS idx_building_neighborhood ON buildings(neighborhood);'))

    print('Creating index  on colum frame in table sv_images...')
    session.execute(text('CREATE INDEX IF NOT EXISTS idx_sv_images_frame ON sv_images(frame);'))

    # ############################
    # # Add detections to database
    # ############################

    # ############################################
    # # Load and process building part predictions
    # ############################################
    loaded_part_dets = []
    with open(parts_inference_fpath, 'r') as json_file:
        for det_parts in json.load(json_file):
            loaded_part_dets.append(_load_detections(det_parts, map_parts))
    loaded_part_dets = [det for det in loaded_part_dets if det is not None]
    n_added_part_dets = add_detections(loaded_part_dets, session, det_classes)

    print(f'Committing detections: {n_added_part_dets} Parts ...')
    session.commit()
    print('Done.\n')
    # ################################################
    # # Load and process building property predictions
    # ################################################
    loaded_properties_dets = []
    with open(props_inference_fpath, 'r') as json_file:
        for det_properties in json.load(json_file):
            loaded_properties_dets.append(_load_detections(det_properties, map_properties))
    loaded_properties_dets = [det for det in loaded_properties_dets if det is not None]
    n_added_prop_dets = add_detections(loaded_properties_dets, session, det_classes)
    # ################################################
    # # Committing detections to db
    # ################################################
    print(f'Committing detections: {n_added_prop_dets} properties...')
    session.commit()
    print('Done.\n')


@click.command(short_help="Link buildings and detections in existing DB.")
@click.argument('db-url', nargs=1)
@click.option("--neighborhood", type=str,
              help="Neighborhood to run matches for.")
def link_db_detections(db_url, neighborhood):
    """Link object detections to building footprints in existing DB.
    Also, consolidates building properties into metadata.
    Parameters
    ----------
    db_url: str
        Database access URL (including username and password if necessary).
    neighborhood: str
        Name of neighborhood to run DB matches for.
    """

    # Link to DB
    session = _get_session(db_url)

    # Loop over all detections and match to buildings
    n_detection_matches = 0
    n_detection_misses = 0

    query = session.query(Detection).filter(Detection.neighborhood == neighborhood)
    for detection in tqdm(query.yield_per(10000),
                          desc='Matching detections to buildings',
                          total=query.count()):

        ################################
        # Look for building intersection
        ################################

        # TODO: Could add a filter to search for buildings within some radius of ray
        build_matches = session.query(Building). \
            filter(Building.neighborhood == neighborhood). \
            filter(ST_Within(Building.centroid, detection.ray_buffer)). \
            filter(ST_Intersects(Building.footprint, detection.detection_ray)).all()

        ###########################################################
        # Handle linkage between linestring and individual building
        ###########################################################

        if not build_matches:
            n_detection_misses += 1
            continue
        # If multiple intersections, find closest building
        elif len(build_matches) > 1:
            dists = []
            # Calc euclidean dist for each building
            for building in build_matches:
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(detection.image.lon, detection.image.lat)
                line.AddPoint(building.lon, building.lat)
                dists.append(line.Length())
            build_match = build_matches[np.argmin(dists)]
        else:
            build_match = build_matches[0]

        build_match.detections.append(detection)
        n_detection_matches += 1

    ##################
    # Print and commit
    ##################
    if (n_detection_matches + n_detection_misses) > 0:
        print(f'Found building matches for {n_detection_matches} detections '
              f'({100 * n_detection_matches / (n_detection_matches + n_detection_misses):0.2f}%)')
    else:
        print('Found 0 building matches. Try checking building footprint file '
              ' for errors/corruption.')
    session.commit()


@click.command(short_help="Export detections as geojson linestrings.")
@click.argument('db-url', nargs=1)
@click.option('--save-fpath', type=str, default='rays.geojson',
              help='Filepath of geojson file to save information to.')
@click.option('--neighborhood', type=str,
              help='Neighborhood to run matches for.')
@click.option('--det_class', type=str, default=None, multiple=True,
              help='Property classes to include (e.g., "window").')
@click.option('--linked-dets-only', type=bool, default=True,
              help='Whether or not to only include detections successfully linked to a building.')
@click.option('--bucker_path', type=str, default="", help='url bucket path ')
def export_detection_geometry(db_url, save_fpath, neighborhood, det_class,
                              linked_dets_only, bucker_path):
    """Generate geojson consisting of linestrings, one per ML detection

    Parameters
    ----------
    db_url: str
        Database access URL (including username and password if necessary).
    save_fpath: str
        Filepath to save the geojson output to.
    neighborhood: str
        Name of neighborhood used to filter for ML detections
    det_class: list or None
        List of class names (e.g., 'complete', 'window', etc.) used to filter
        detections.
    linked_dets_only: bool
        Whether to only export detections that are matched to a building.
    bucker_path: str
        Url bucket path.
    """

    # Link to DB
    session = _get_session(db_url)
    if bucker_path:
        if bucker_path.endswith("/"):
            bucker_path = bucker_path[:-1]

    ########################
    # Get all detection rays
    ########################
    print('Getting desired detections...')
    detections = session.query(Detection, Detection.detection_ray.ST_AsGeoJSON()) \
        .outerjoin(Image, Detection.image_id == Image.id) \
        .filter(Detection.neighborhood == neighborhood)
    if det_class:
        print(f'Filtering for classes: {str(det_class)}...')
        detections = detections.filter(Detection.class_str.in_(det_class))
    if linked_dets_only:
        print('Filtering detections that don\'t have matching building...')
        detections = detections.filter(Detection.building_id.isnot(None))

    detections = detections.add_columns(Image.subfolder, Image.image_fname)
    n_rows = detections.count()
    print(f'Found {n_rows} detections. Pulling necessary info...')

    ################################
    # Dump detection rays to geojson
    ################################
    geojson_rays = {"type": "FeatureCollection",
                    "name": f'{neighborhood}_rays',
                    "crs": {"type": "name", "properties":
                        {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                    "features": []}

    for det, geom, image_subfolder, image_image_fname in tqdm(detections.yield_per(10000),
                                                              desc='Constructing geometries', total=n_rows):

        image_path = f'{image_subfolder}/{image_image_fname}' if image_subfolder and image_image_fname else None
        if bucker_path and image_path:
            image_path = "/".join([bucker_path,*image_path.split("/")[-3:]])

        properties = dict(class_str=det.class_str,
                          image_id=getattr(det, 'image_id', 'None'),
                          image_path=image_path,
                          confidence=det.confidence)

        geojson_rays['features'].append({'type': "Feature",
                                         'geometry': json.loads(geom),
                                         'properties': properties})

    print('Dumping information to geojson...')
    # Construct list of all rays
    with open(save_fpath, 'w') as geoj_f:
        json.dump(geojson_rays, geoj_f)

    print(f'Saved {len(geojson_rays["features"])} ray linestrings to {save_fpath}')
