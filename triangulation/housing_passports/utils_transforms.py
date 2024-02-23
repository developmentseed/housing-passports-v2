"""
Transform detected objects from image to map coordinates

@author: developmentseed
"""
import csv

import numpy as np
from osgeo import ogr
from pyproj import Geod
from pyproj import CRS
# import pyproj 
from shapely.geometry import LineString, Point, Polygon, box
from pyproj import Transformer
from geoalchemy2.functions import ST_Intersects, ST_AsText
from shapely.wkt import loads

transformer_4326_3857 = Transformer.from_crs("epsg:4326", "epsg:3857")
transformer_3857_4326 = Transformer.from_crs("epsg:3857", "epsg:4326")

def load_geo_layer(fpath, ogr_driver='GeoJSON'):
    """Load a geojson file using GDAL and return layer"""
    driver = ogr.GetDriverByName(ogr_driver)
    dataSource = driver.Open(fpath, 0) # 0 means read-only. 1 means writeable.

    # Check to see if geojson is found.
    if dataSource is None:
        print('Could not open {}'.format(fpath))
        return

    print('Opened {}'.format(fpath))
    layer = dataSource.GetLayer()

    for ind in range(0, layer.GetFeatureCount()):
        feat = layer.GetFeature(ind)
        print(f'{ind}: {feat}')

    print('Found {} features'.format(layer.GetFeatureCount()))

    return layer


def csv_gps_to_dict(fpath_csv):
    """Convert GPS infromation from CSV into dict for faster lookup later"""

    # Add any desired properties here using the string column name
    desired_cols = ['latitude[deg]', 'longitude[deg]', 'heading[deg]']
    gps_dict = {}

    with open(fpath_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            # Make sure to include exactly 5 decimal places to match image names
            gps_time = '{:.05f}'.format(float(row['gps_seconds[s]']))

            gps_dict[gps_time] = {}
            for key in desired_cols:
                gps_dict[gps_time][key] = float(row[key])

    return gps_dict


def get_LR_visual_extents(gps_heading, fov_extent=90.):
    """Find the min/max visual degrees of the L/R camera based on heading

    Parameters
    ----------
    gps_heading: float
        Heading of car on interval [0, 360).
    fov_extent: float
        Field of view (degrees) of camera

    Returns
    -------
    vis_extent: dict
        Visual extents (in degrees) of right and left view.
    """

    # Get left and right min/max
    half_window = fov_extent / 2
    vis_extent = dict(l_min=(gps_heading + 270 - half_window),
                      l_max=(gps_heading + 270 + half_window),
                      r_min=(gps_heading + 90 - half_window),
                      r_max=(gps_heading + 90 + half_window))

    # Correct for minimum angles > 360 deg
    if vis_extent['l_min'] >= 360:
        vis_extent['l_min'] -= 360
        vis_extent['l_max'] -= 360

    if vis_extent['r_min'] >= 360:
        vis_extent['r_min'] -= 360
        vis_extent['r_max'] -= 360

    return vis_extent


def get_LR_visual_extents_dict(gps_dict, fov_extent=90.,
                               heading_key='heading[deg]'):
    """Find the min/max visual degrees of the L/R camera based on headings

    Parameters
    ----------
    gps_dict: dict
        Set of lat/lon points based on GPS coords and headings keyed by time
        stamp (for fast lookup).
    fov_extent: float
        Field of view (degrees) of camera
    heading_key: string
        Key name of heading variable used to calculate FOV extents.

    Returns
    -------
    vis_extents: dict
        Visual extents (in degrees) of right and left view keyed by same GPS
        time stamps.
    """

    vis_extents = {}

    for key in gps_dict.keys():
        heading = gps_dict[key][heading_key]
        vis_extents[key] = get_LR_visual_extents(heading, fov_extent)

    return vis_extents


def interpolate(norm_prop, min_val, max_val):
    """Interpolate between two extremes (e.g., view angles in an image)

    Parameters
    ----------
    norm_prop: float
        Value to interpolate. Should be normalized between 0 and 1.
    min_val: float
    max_val: float

    Returns
    -------
    interp_val: float
    """
    if not 0 <= norm_prop <= 1:
        raise ValueError(f'norm_prop must be on [0, 1]. Received: {norm_prop}')
    if min_val > max_val:
        raise ValueError('max_val is less than max_val')

    return min_val + (max_val - min_val) * norm_prop

def generate_buffer(lon, lat, distance):
    """Generate a Buffer from lon and lat of the image

    Parameters
    ----------
    lon: float
        Longitude point in deg
    lat: float
        Latitude point in deg
    distance: float
        Distance away from start lat/lon coordinate in meters

    Returns
    -------
    polygon: str
        WKT specifying buffer polygon
    
    example
    -------
    print(generate_buffer(100.377518458264, -0.9378243361254379, 50))
    """
    x, y = transformer_4326_3857.transform(lat, lon)
    point = Point(x,y)
    polygon = point.buffer(distance)
    polygonSimple = polygon.simplify(5, preserve_topology=False)
    proj_buffer_points = []
    for point in list(polygonSimple.exterior.coords):
        x = point[0]
        y = point[1]
        x, y = transformer_3857_4326.transform(x, y)
        proj_buffer_points.append((y,x))
    polygonSimple = Polygon(proj_buffer_points)
    return polygonSimple.wkt


def generate_ray(lon_start, lat_start, az, distance=20):
    """Generate a linestring object from a start location, angle, and distance

    Parameters
    ----------
    lon: float
        Longitude point in deg
    lat: float
        Latitude point in deg
    az: float
        Azimuth heading used to generate 2nd line point
    distance: float
        Distance away from start lat/lon coordinate in meters

    Returns
    -------
    line: str
        WKT specifying ray linestring
    """

    # Interpolate end point using a start point, heading, and distance
    geod = Geod(ellps='WGS84')
    lon_end, lat_end, az_end = geod.fwd(lon_start, lat_start, az, distance)

    # Create line from start and (derived) end point
    line = LineString([(lon_start, lat_start), (lon_end, lat_end)])

    return line.wkt


def calc_pt_dist_to_geom(xy_pt, geoms):
    """Get distance from point to polygon centroid(s)

    Parameters
    ----------
    xy_pt: tuple of float
        x and y coordinate for point
    geoms: shapely.geometry or list of shapely.geometry
        Geometries to calculate distance to

    Returns
    -------
    dists: float or list of float
        Distance from point to each polygon centroid
    """
    def l2_dist(x1, y1, x2, y2):
        """Calculate euclidean distance"""
        return np.sqrt(np.square(x2 - x1) + np.square(y2 - y1))

    # Error checking and make sure geoms is a list
    if not isinstance(geoms, list):
        geoms = [geoms]
    if not geoms:
        raise ValueError('No geometries found')

    dists = []
    for geom in geoms:
        dists.append(l2_dist(xy_pt[0], xy_pt[1],
                             geom.centroid.x, geom.centroid.y))

    # Return single distance or distance to each geometry
    if len(dists) == 1:
        return dists[0]

    return dists

def generate_buffer_ray(wkt_linestring, distance=15):
    """Get buffer of detection ray

    Parameters
    ----------
    wkt_linestring: detection ray lineString
    distance: distance to generate the buffer

    Returns
    -------
    polygon wkt: String of polygon as wkt format

    example
    -------
    print(generate_buffer_ray('LINESTRING (100.379621266922 -0.9399297362403251, 100.3794650645071 -0.9398403340425333)'))
    """
    lineString_4326 = loads(wkt_linestring)
    # Reproject LineString
    array_coords_3857 = []
    for point in list(lineString_4326.coords):
        x = point[0]
        y = point[1]
        x, y = transformer_4326_3857.transform(y, x)
        array_coords_3857.append((y, x))
    lineString_3857 = LineString(array_coords_3857)
    # # Buffer the lineString
    polygon_3857 = lineString_3857.buffer(distance)
    proj_buffer_points = []
    for point in list(polygon_3857.exterior.coords):
        x = point[0]
        y = point[1]
        x, y = transformer_3857_4326.transform(y, x)
        proj_buffer_points.append((y, x))
    polygon_4326 = Polygon(proj_buffer_points)
    bounds = polygon_4326.bounds
    bounds_poly = box(minx=bounds[0], miny=bounds[1], maxx=bounds[2], maxy=bounds[3])
    return bounds_poly.wkt
