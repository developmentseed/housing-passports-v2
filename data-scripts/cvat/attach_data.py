"""
Script for merge original data and cvat output
"""
from utils.index import read_geojson, write_geojson, read_csv, write_dictlist2csv
from tqdm import tqdm
import fire


def combine_resources(cvat_csv, original_geojson, geojson_output, csv_output_trajectory):
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
    # housing_passports formats
    trajectories_out = []
    data_out = []
    for feature in tqdm(features, desc="Hp  format"):
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
            "subfolder": "/".join(['data', *path_seq[-3:-1]])
        }
        trajectories_out.append(trajectory)

    write_dictlist2csv(csv_output_trajectory, trajectories_out)


def main():
    fire.Fire(combine_resources)


if __name__ == "__main__":
    main()
