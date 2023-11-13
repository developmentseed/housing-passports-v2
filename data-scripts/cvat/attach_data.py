"""
Script for merge original data and cvat output
"""
from utils.index import read_geojson, write_geojson, read_csv, write_dictlist2csv
from tqdm import tqdm
import fire


def combine_resources(cvat_csv, original_geojson, geojson_output, csv_output):
    features = read_geojson(original_geojson)
    csv_data = read_csv(cvat_csv)

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
    # housing_passports format
    data_out = []
    for feature in tqdm(features, desc="Hp  format"):
        props = feature.get("propeties", {})
        lat, lng = feature.get("geometry", {}).get("coordinates")
        for box in props.get("box", []):
            data_ = {
                "heading[deg]": props.get("compass_angle"),
                "image_fname": f"{box.get('img_path')}/{box.get('img_name')}",
                "frame": box.get('img_name', ""),
                "latitude[deg]": lat,
                "longitude[deg]": lng,
                "box_label": box.get("box_label", ""),
                "box_xtl": box.get("box_xtl", ""),
                "box_ytl": box.get("box_ytl", ""),
                "box_xbr": box.get("box_xbr", ""),
                "box_ybr": box.get("box_ybr", ""),
                "box_attr_building_condition": box.get("box_attr_building_condition", ""),
                "box_attr_building_material": box.get("box_attr_building_material", ""),
                "box_attr_building_use": box.get("box_attr_building_use", ""),
                "box_attr_building_security": box.get("box_attr_building_security", ""),
                "box_attr_building_completeness": box.get("box_attr_building_completeness", ""),
            }
            data_out.append(data_)
    write_dictlist2csv(csv_output, data_out)


def main():
    fire.Fire(combine_resources)


if __name__ == "__main__":
    main()
