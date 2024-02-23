"""
Script for merge original data and detections
"""
import json

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
    IMAGE_SIDE,
)
from mapillary.heading import compass_to_cartesian
from tqdm import tqdm
import fire
import geopandas as gpd
from copy import deepcopy
from shapely import wkb
from shapely.geometry import shape


def pixel2proportion(box_values, w=1024, h=1024, r=6):
    # x_min, y_min, x_max, y_max
    return [
        round(
            (box_values[0] / w),
            r,
        ),
        round(
            (box_values[1] / h),
            r,
        ),
        round(
            (box_values[2] / w),
            r,
        ),
        round(
            (box_values[3] / h),
            r,
        ),
    ]


def add_geom(features):
    for i in tqdm(features, desc="add geom"):
        i["geom"] = shape(i.get("geometry"))
    return features


def rm_geom(features):
    for i in features:
        if "geom" in i.keys():
            del i["geom"]
    return features


def include_geom(features, features_area):
    for feature in tqdm(features, desc="include_geom"):
        for feature_area in features_area:
            if feature_area["geom"].contains(feature["geom"].centroid):
                feature["properties"]["neighborhood"] = feature_area["properties"][
                    "neighborhood"
                ]
                break

    return features


def combine_resources(
    predictions_csv,
    original_geojson,
    gpkg_buildings_file,
    prefix_path_images,
    neighborhood,
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
    - predictions_csv (str): Path CSV file containing predictions csv.
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

    features_areas_ = read_geojson(neighborhood)
    features_areas__ = add_geom(features_areas_)

    features_ = read_geojson(original_geojson)
    features__ = add_geom(features_)

    features_all = include_geom(features__, features_areas__)
    features = rm_geom(features_all)

    # df_polygons = gpd.read_file(gpkg_buildings_file)

    csv_predictions_data = read_csv(predictions_csv)
    print("total_csv", len(csv_predictions_data))
    # group csv data
    csv_groups = {}
    for box in tqdm(csv_predictions_data, desc="group csv data"):
        fake_key = box.get("image_name").strip()
        box["boxes"] = json.loads(box.get("boxes"))
        box["boxes_float"] = json.loads(box.get("boxes_float", "[]"))
        box["boxes_int"] = json.loads(box.get("boxes_int", "[]"))

        if not csv_groups.get(fake_key):
            csv_groups[fake_key] = []
        csv_groups[fake_key].append(box)

    for feature in tqdm(features, desc="merge features and csv"):
        props = feature.get("properties")
        # side = props.get("image_path").split("_")[-1].split(".")[0]
        compass_angle_ = props.get("compass_angle")
        # if side == "left":
        #     compass_angle = round((compass_angle_ + 90) % 360, 2)
        # else:
        #     compass_angle = round((compass_angle_ - 90 + 360) % 360, 2)

        props["compass_angle_fix"] = compass_angle_
        fake_key = props.get("image_path", "").split("mapillary_images_new/")[1].strip()
        props["boxes"] = csv_groups.get(fake_key, [])

    write_geojson(geojson_merge_output, features)
    # housing_passports formats
    trajectories_out = []
    building_props_out = []
    building_parts_out = []

    for feature in tqdm(features, desc="Hp  create format"):
        props = feature.get("properties", {})
        lng, lat = feature.get("geometry", {}).get("coordinates")
        path_seq = props.get("image_path", "").strip().split("/")
        image_name = path_seq[-1]
        neighborhood_ = props.get("neighborhood")

        image_path_ = "/".join([prefix_path_images, *path_seq[-3:-1]])
        cam = IMAGE_SIDE.get(path_seq[-2], 0)
        frame = image_name.split(".")[0]
        trajectory = {
            "heading[deg]": props.get("compass_angle_fix"),
            "image_fname": image_name,
            "frame": frame,
            "latitude[deg]": lat,
            "longitude[deg]": lng,
            "cam": cam,
            "neighborhood": neighborhood_,  # default
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
            "neighborhood": neighborhood_,
        }
        box_building_props = deepcopy(box_props)
        # box_building_parts = deepcopy(box_props)

        trajectories_out.append(trajectory)

        for box_meta in props.get("boxes", []):
            box = pixel2proportion(box_meta.get("boxes"))

            # check building parts
            for prop_key in BUILDING_PROPS_DICT.keys():
                if box_meta.get(prop_key):
                    new_key = BUILDING_PROPS.get(box_meta.get(prop_key))
                    box_building_props["detection_boxes"].append(deepcopy(box))
                    box_building_props["detection_classes"].append(new_key)
                    # add logic for score
                    box_building_props["detection_scores"].append(
                        float(box_meta.get("box_scores", "1"))
                    )

        building_props_out.append(deepcopy(box_building_props))
    # write_json(BUILDING_PROPS, )
    # write files
    write_dictlist2csv(csv_output_trajectory, trajectories_out)
    # write props
    write_json(props_inference_file, building_props_out)
    write_json(parts_inference_file, building_parts_out)

    write_pbtxt_content(props_map_file, BUILDING_PROPS)
    write_pbtxt_content(parts_map_file, BUILDING_PARTS)

    # write shp
    # df_polygons = df_polygons.to_crs(4326)
    # df_polygons["geometry"] = df_polygons["geometry"].apply(
    #     lambda geom: geom
    #     if geom.is_empty
    #     else wkb.loads(wkb.dumps(geom, output_dimension=2))
    # )

    # df_neighborhood = gpd.read_file(neighborhood)

    # df_polygons_centroids = df_polygons.copy()
    # df_polygons_centroids.geometry = df_polygons.geometry.centroid
    #
    # joined = gpd.sjoin(df_polygons_centroids, df_neighborhood, how="inner", op="within")
    # df_polygons["neighborhood"] = joined["neighborhood"]

    # keys file
    write_json(
        props_keys_file, {k: list(v.keys()) for k, v in BUILDING_PROPS_DICT.items()}
    )
    write_json(
        part_keys_file, {k: list(v.keys()) for k, v in BUILDING_PARTS_DICT.items()}
    )
    # df_polygons.to_file(shp_buildings_file, driver="ESRI Shapefile")


def main():
    fire.Fire(combine_resources)


if __name__ == "__main__":
    main()
