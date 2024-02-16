import sys
import json
from geojson import Feature, FeatureCollection as fc

with open(sys.argv[1], encoding='utf8') as f:
        features = json.load(f)["features"]

for index, feature in enumerate(features):
    feature['properties']['neighborhood'] = 'padang'
    del feature['properties']['neighborho']

# Save
f = open(sys.argv[2], "w")
f.write(json.dumps(fc(features)).encode('utf8').decode())
f.close()
