"""
Script for merge original data and detections
"""
from utils.utils import (
    read_geojson,
    write_geojson,
    read_csv,
    write_dictlist2csv,
    write_json,
    write_pbtxt_content,
)
from utils.constants import (
    BUILDING_PARTS_DICT,
    BUILDING_PROPS_DICT,
    BUILDING_PARTS,
    BUILDING_PROPS,
    BUILDING_PROPERTIES_BOX_CVAT,
    IMAGE_SIDE,
)
from mapillary.heading import compass_to_cartesian
from tqdm import tqdm
import fire
import geopandas as gpd
from copy import deepcopy
from shapely import wkb


def pixel2proportion(box_meta_dict, x, y):
    return round(
        float(box_meta_dict.get(x, "")) / float(box_meta_dict.get(y, "")),
        3,
    )


def combine_resources(
    annotation_properties_csv,
    annotation_parts_csv,
    original_geojson,
    gpkg_buildings_file,
    prefix_path_images,
    shp_buildings_file,
    geojson_merge_output,
    csv_output_trajectory,
    props_inference_file,
    props_map_file,
    parts_inference_file,
    parts_map_file,
    props_keys_file,
    part_keys_file,
):
    """
    Allows you to create the necessary files to run db_compilation.sh from housing_passports v1.

    This function integrates the annotated cvat data in csv format, the original points and the buildings to combine and validate them.

    Parameters:
    - annotation_properties_csv (str): Path CSV file containing annotation properties.
    - annotation_parts_csv (str): Path CSV file containing annotation parts.
    - original_geojson (str): Path GeoJSON points file.
    - gpkg_buildings_file (str): Path GeoPackage file with building data.
    - prefix_path_images (str): Prefix path for images.
    - shp_buildings_file (str): Path output Shapefile containing building data.
    - geojson_merge_output (str): Path output merged GeoJSON file.
    - csv_output_trajectory (str): Path output CSV file with trajectory information.
    - props_inference_file (str): Path output JSON file with properties inference data.
    - props_map_file (str): Path output protobuf text file mapping properties.
    - parts_inference_file (str): Path output JSON file with parts inference data.
    - parts_map_file (str): Path output protobuf text file mapping parts.
    - props_keys_file (str): Path output JSON file with properties keys.
    - part_keys_file (str): Path output JSON file with parts keys.

    """

    features = read_geojson(original_geojson)
    csv_data_props = read_csv(annotation_properties_csv)
    csv_data_parts = read_csv(annotation_parts_csv)

    list_data_annotation = [*csv_data_props, *csv_data_parts]
    df_polygons = gpd.read_file(gpkg_buildings_file)
    # group csv data
    csv_groups = {}
    for box in tqdm(list_data_annotation, desc="join data"):
        fake_key = f'{box["img_path"]}/{box["img_name"]}'
        if not csv_groups.get(fake_key):
            csv_groups[fake_key] = []
        csv_groups[fake_key].append(box)

    for feature in tqdm(features, desc="merge features"):
        props = feature["properties"]
        props["compass_angle_fix"] = compass_to_cartesian(props.get("compass_angle"))
        fake_key = "/".join(props.get("image_path", "").split("/")[-3:])
        props["box"] = csv_groups.get(fake_key, [])

    write_geojson(geojson_merge_output, features)
    # housing_passports formats
    trajectories_out = []
    building_props_out = []
    building_parts_out = []

    for feature in tqdm(features, desc="Hp  create format"):
        props = feature.get("properties", {})
        lng, lat = feature.get("geometry", {}).get("coordinates")
        path_seq = props.get("image_path", "").split("/")
        image_name = path_seq[-1]
        if not props.get("box", []):
            continue
        image_path_ = "/".join([prefix_path_images, *path_seq[-3:-1]])
        cam = IMAGE_SIDE.get(path_seq[-2], 0)
        frame = image_name.split(".")[0]
        trajectory = {
            "heading[deg]": compass_to_cartesian(props.get("compass_angle")),
            "image_fname": image_name,
            "frame": frame,
            "latitude[deg]": lat,
            "longitude[deg]": lng,
            "cam": cam,
            "neighborhood": "n1",
            "subfolder": image_path_,
        }
        box_props = {
            "detection_scores": [],
            "detection_classes": [],
            "detection_boxes": [],
            "image_fname": image_name,
            "subfolder": image_path_,
            "cam": cam,
            "frame": frame,
            "neighborhood": "n1",
        }
        box_building_props = deepcopy(box_props)
        box_building_parts = deepcopy(box_props)

        trajectories_out.append(trajectory)

        for box_meta in props.get("box", []):
            box = [
                pixel2proportion(box_meta, "box_xtl", "img_width"),
                pixel2proportion(box_meta, "box_ytl", "img_height"),
                pixel2proportion(box_meta, "box_xbr", "img_width"),
                pixel2proportion(box_meta, "box_ybr", "img_height"),
            ]

            box_label = box_meta.get("box_label")
            if not box_label:
                continue
            if box_label == "building_properties":
                for prop_key in BUILDING_PROPERTIES_BOX_CVAT:
                    if box_meta.get(prop_key):
                        new_key = BUILDING_PROPS.get(box_meta.get(prop_key))
                        box_building_props["detection_boxes"].append(deepcopy(box))
                        box_building_props["detection_classes"].append(new_key)
                        box_building_props["detection_scores"].append(1)

            else:
                new_key = BUILDING_PARTS.get(box_label)
                box_building_parts["detection_boxes"].append(deepcopy(box))
                box_building_parts["detection_classes"].append(new_key)
                box_building_parts["detection_scores"].append(1)

        building_props_out.append(deepcopy(box_building_props))
        building_parts_out.append(deepcopy(box_building_parts))

    # write_json(BUILDING_PROPS, )
    # write files
    write_dictlist2csv(csv_output_trajectory, trajectories_out)
    # write props
    write_json(props_inference_file, building_props_out)
    write_json(parts_inference_file, building_parts_out)

    write_pbtxt_content(props_map_file, BUILDING_PROPS)
    write_pbtxt_content(parts_map_file, BUILDING_PARTS)

    # write shp
    df_polygons["neighborhood"] = "n1"
    df_polygons = df_polygons.to_crs(4326)
    df_polygons["geometry"] = df_polygons["geometry"].apply(
        lambda geom: geom
        if geom.is_empty
        else wkb.loads(wkb.dumps(geom, output_dimension=2))
    )

    df_polygons.to_file(shp_buildings_file, driver="ESRI Shapefile")
    # keys file
    write_json(
        props_keys_file, {k: list(v.keys()) for k, v in BUILDING_PROPS_DICT.items()}
    )
    write_json(
        part_keys_file, {k: list(v.keys()) for k, v in BUILDING_PARTS_DICT.items()}
    )


def main():
    fire.Fire(combine_resources)


if __name__ == "__main__":
    main()
