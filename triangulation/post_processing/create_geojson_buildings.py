"""
Utils to export buildings from the db to Geojson file

python create_geojson_buildings.py <string db connection> <neighborhood> <outputFile>

python create_geojson_buildings.py postgresql://postgres:1234@hp_db:5432/db_passport chacarita full_buildings.geojson
"""

import os
import os.path as op
import json
import sys

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Integer
from sqlalchemy import func
from sqlalchemy.orm import subqueryload

from housing_passports.db_classes import Image, Building, Detection, Base

db_url = sys.argv[1]
neighborhood = sys.argv[2]
fpath_geojson = sys.argv[3]
s3_fpath = sys.argv[4]
if s3_fpath.endswith("/"):
    s3_fpath = s3_fpath[:-1]

# Create database connection
engine = create_engine(db_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Add neighborhood in case filter by it
detection_subquery = (
    session.query(Detection).filter(Detection.building_id == Building.id).subquery()
)

building_query = (
    session.query(Building, func.ST_AsGeoJSON(Building.footprint))
    .filter(Building.neighborhood == neighborhood)
    .options(subqueryload(Building.detections).subqueryload(Detection.image))
)

print(f"Found {building_query.count()} buildings.\n")

# Geojson template
geojson_buildings = {
    "type": "FeatureCollection",
    "name": f"buildings_{neighborhood}",
    "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    "features": [],
}

# Drop each building (geometry and properties) into geojson
for building, geom in building_query.all():
    detections_array = []
    for detection in building.detections:
        image_path = "/".join(str(detection.image.subfolder).split("/")[-2:])
        detection_info = {
            "detection_id": detection.id,
            "image_id": detection.image.id,
            "class_id": detection.class_id,
            "class_str": detection.class_str,
            "confidense": detection.confidence,
            "image_filename": f"{s3_fpath}/{image_path}/{detection.image.image_fname}"
        }
        detections_array.append(detection_info)

    metadata = building.building_metadata
    metadata["detections"] = detections_array
    geojson_buildings["features"].append(
        {
            "type": "Feature",
            "geometry": json.loads(geom),
            "properties": building.building_metadata,
        }
    )

# Write out geojson file
with open(fpath_geojson, "w") as geojson_f:
    json.dump(geojson_buildings, geojson_f)
print(f"Saved geojson to: {fpath_geojson}")
