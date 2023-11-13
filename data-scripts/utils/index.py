import json
import math
from geojson import FeatureCollection
import csv


def read_geojson(input_file):
    """Read a geojson file and return a list of features

    Args:
        input_file (str): Location on geojson file

    Returns:
        list: list fo features
    """
    fc = []
    with open(input_file, "r", encoding="utf8") as f:
        cf = json.load(f)["features"]
    return cf


def write_geojson(output_file, list_features):
    """Write geojson files

    Args:
        output_file (str): Location of ouput file
        list_features (list): List of features
    """
    with open(output_file, "w") as f:
        json.dump(FeatureCollection(list_features), f)


def read_csv(image_csv_fpath):
    """Read a csv file and return a dict

    Args:
        image_csv_fpath (str): Location on csv file

    Returns:
        list: list  of elements
    """

    with open(image_csv_fpath, "r") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        rows = list(reader)
        return rows


def write_dictlist2csv(output_file, list_features):
    """Write csv files

    Args:
        output_file (str): Location of ouput file
        list_features (list): List of features
    """
    if not list_features:
        return None
    with open(output_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(list_features[0].keys()))
        writer.writeheader()
        writer.writerows(list_features)
