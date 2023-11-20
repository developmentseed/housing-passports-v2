"""
Script for merge original data and cvat output
"""
from utils.index import (
    read_geojson,
    write_geojson,
    read_csv,
    write_dictlist2csv,
    write_json,
    write_pbtxt_content,
)
from tqdm import tqdm
import fire
import geopandas as gpd

BUILDING_PROPERTIES = [
    "box_attr_building_condition",
    "box_attr_building_material",
    "box_attr_building_use",
    "box_attr_building_security",
    "box_attr_building_completeness",
]

BUILDING_VALUES = {
    "brick_or_cement-concrete_block": 1,
    "plaster": 2,
    "wood_polished": 3,
    "wood_crude-plank": 4,
    "adobe": 5,
    "corrugated_metal": 6,
    "stone_with_mud-ashlar_with_lime_or_cement": 7,
    "container-trailer": 8,
    "plant_material": 9,
    "mix-other-unclear": 10,
    "complete": 11,
    "incomplete": 12,
    "residential": 13,
    "mixed": 14,
    "commercial": 15,
    "critical_infrastructure": 16,
    "unsecured": 17,
    "secured": 18,
    "fair": 19,
    "poor": 20,
    "good": 21,
}


def combine_resources(
    cvat_csv,
    original_geojson,
    geojson_output,
    csv_output_trajectory,
    props_inference_file,
    props_map_file,
    gpkg_buildings_file,
    shp_buildings_file,
):
    features = read_geojson(original_geojson)
    csv_data = read_csv(cvat_csv)
    df_polygons = gpd.read_file(gpkg_buildings_file)
    # group csv data
    csv_groups = {}
    for box in tqdm(csv_data, desc="join data"):
        fake_key = f'{box["img_path"]}/{box["img_name"]}'
        if not csv_groups.get(fake_key):
            csv_groups[fake_key] = []
        csv_groups[fake_key].append(box)

    for feature in tqdm(features, desc="merge features"):
        props = feature["properties"]
        fake_key = "/".join(props.get("image_path", "").split("/")[-3:])
        props["box"] = csv_groups.get(fake_key, [])

    write_geojson(geojson_output, features)
    # housing_passports formats
    trajectories_out = []
    # building_parts = []
    building_props_out = []

    for feature in tqdm(features, desc="Hp  create format"):
        props = feature.get("properties", {})
        lat, lng = feature.get("geometry", {}).get("coordinates")
        path_seq = props.get("image_path", "").split("/")
        image_name = path_seq[-1]

        trajectory = {
            "heading[deg]": props.get("compass_angle"),
            "image_fname": image_name,
            "frame": image_name.split(".")[0],
            "latitude[deg]": lat,
            "longitude[deg]": lng,
            "cam": path_seq[-2],
            "neighborhood": "n1",
            "subfolder": "/".join(["data", *path_seq[-3:-1]]),
        }
        box_building_props = {
            "detection_scores": [],
            "detection_classes": [],
            "detection_boxes": [],
            "image_fname": image_name,
            "subfolder": "/".join(["data", *path_seq[-3:-1]]),
            "cam": path_seq[-2],
            "frame": image_name.split(".")[0],
            "neighborhood": "n1",
        }
        trajectories_out.append(trajectory)

        for box_meta in props.get("box", []):
            box = [
                float(box_meta.get("box_xtl", "")),
                float(box_meta.get("box_ytl", "")),
                float(box_meta.get("box_xbr", "")),
                float(box_meta.get("box_ybr", "")),
            ]
            for prop_key in BUILDING_PROPERTIES:
                if box_meta.get(prop_key):
                    new_key = BUILDING_VALUES.get(box_meta.get(prop_key))
                    box_building_props["detection_boxes"].append(box)
                    box_building_props["detection_classes"].append(new_key)

        building_props_out.append(box_building_props)
    # write_json(BUILDING_VALUES, )
    # write files
    write_dictlist2csv(csv_output_trajectory, trajectories_out)
    # write props
    write_json(props_inference_file, building_props_out)
    write_pbtxt_content(props_map_file, BUILDING_VALUES)

    # write shp
    df_polygons["neighborhood"] = "n1"
    df_polygons.to_file(shp_buildings_file, driver="ESRI Shapefile")


def main():
    fire.Fire(combine_resources)


if __name__ == "__main__":
    main()
