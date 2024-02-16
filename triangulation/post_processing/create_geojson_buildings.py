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

from housing_passports.db_classes import Image, Building, Detection, Base

db_url = sys.argv[1]
neighborhood = sys.argv[2]
fpath_geojson = sys.argv[3]

# Create database connection
engine = create_engine(db_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Add neighborhood in case filter by it
building_query = session.query(Building, func.ST_AsGeoJSON(Building.footprint)). \
    filter(Building.neighborhood == neighborhood)

print(f'Found {building_query.count()} buildings.\n')

# Geojson template
geojson_buildings = {"type": "FeatureCollection",
                     "name": f"buildings_{neighborhood}",
                     "crs": {"type": "name", "properties":
                             {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                     "features": []}

# Drop each building (geometry and properties) into geojson
for building, geom in building_query.all():
    geojson_buildings['features'].append({'type': "Feature",
                                          'geometry': json.loads(geom),
                                          'properties':  building.building_metadata})

# Write out geojson file
with open(fpath_geojson, 'w') as geojson_f:
    json.dump(geojson_buildings, geojson_f)
print(f'Saved geojson to: {fpath_geojson}')
