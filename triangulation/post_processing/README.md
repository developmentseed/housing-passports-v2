
# Runing HP Database population under Docker

In this section, we have the environment work that we need to build the model evaluations and run post-processing:

**Containers**

- `hpnb`: This is used for running the notebooks on the model evaluation.

- `tfs_properties`:  Api service for `developmentseed/building_properties:v1`

- `tfs_parts`: Api service for `developmentseed/building_parts:v1`

- `hpdb` : Postgis database

-  `hpdev`: Cotainer used for upload tthe files into the database.

### Build docker images


```
docker-compose build
```

### Execute DB

```
docker-compose up hpdb
```

### Access to Dev environment

```
docker-compose run hpdev
```

Testing access to DB

```
pg_isready -h hpdb -p 5432
```

### Insert information into DB

Dump buildings, images, and detections into database. Also, link images to detections.

Start the DB `docker-container up hpdb -d`

Start the contianer to interact with the DB : `docker-container run hpdev`


```bash
COUNTRY=Indonesia
CITY=padang
PG_CONNECTION=postgresql://postgres:1234@hpdb:5432/db_passport

passport_db_export ${PG_CONNECTION} \
--trajectory-fpath=<path_to>/trajectory/padang.csv \
--geomfile-fpath=<path_to>/rooftop/padang.shp \
--neighborhood=${CITY} \
--props-inference-fpath=<path_to>/prediction/prediction_filtered_properties.json \
--parts-inference-fpath=<path_to>prediction/prediction_filtered_parts.json \
--parts-map-fpath=<path_to>/labels/building_parts.pbtxt \
--props-map-fpath=<path_to>/labels/building_properties.pbtxt

# Link detections to buildings within database.
passport_link_db_detections ${PG_CONNECTION} \
--neighborhood=${CITY}

# Distill many detections into single attribute per category
# This sets attributes according to highest total confidence (for building properties) or max number observed instances (building parts)
passport_distill_metadata \
${PG_CONNECTION} \
--fpath-parts=<path_to>/labels/building_parts_list.json \
--fpath-property-groups=<path_to>/labels/building_properties_categorized.json \
--neighborhood=${CITY}

```

**Note**

- Trajectory file format `--trajectory-fpath=<path_to>/trajectory/padang.csv`

```csv
heading[deg],image_fname,frame,latitude[deg],longitude[deg],cam,neighborhood,subfolder
238.81604587884,ladybug_14062044_20190628_141526_Cube_000000_Cam1_879_090-0881.jpg,ladybug_14062044_20190628_141526_Cube_000000,-0.937739981443431,100.377668449777,"1",padang,PADANG_01
238.81604587884,ladybug_14062044_20190628_141526_Cube_000000_Cam3_879_090-0881.jpg,ladybug_14062044_20190628_141526_Cube_000000,-0.937739981443431,100.377668449777,"3",padang,PADANG_01
238.918032366373,ladybug_14062044_20190628_141526_Cube_000001_Cam1_880_091-3497.jpg,ladybug_14062044_20190628_141526_Cube_000001,-0.93774492395104,100.377660678983,"1",padang,PADANG_01
...
```

- Rooftop shapefile format `--geomfile-fpath=<path_to>/rooftop/padang.shp`

Building footprints metadata should include an `Id` unique identification, it should be  coordinated with the client(WB), and a colum called `neighborh`(neighborhood).

- Inference detection file format

```
--props-inference-fpath=<path_to>/prediction/prediction_filtered_properties.json
--parts-inference-fpath=<path_to>prediction/prediction_filtered_parts.json
```

```json
  {
      "detection_scores": [],
      "detection_classes": [],
      "detection_boxes": [],
      "image_fname": "GEP/DRONE2/ASUNCION/252a_CubeImage/000000_Cam3.jpg",
      "subfolder": "252a_CubeImage",
      "cam": 1
  }
```

Some images deliverer by WB need to be formatted in something like `252a_CubeImage_000000_Cam3.jpg`

- PBtxt format

```
--parts-map-fpath=<path_to>/labels/building_parts.pbtxt
--props-map-fpath=<path_to>/labels/building_properties.pbtxt
```

Building parts

```
item {
  id: 1
  name: 'window'
}
item {
  id: 2
  name: 'door'
} ....
```

Building properties

```
item {
  id: 1
  name: 'brick_or_cement-concrete_block'
}
item {
  id: 2
  name: 'plaster'
}
item {
  id: 3
  name: 'wood_polished'
} ....
```

- Filer format for distill  detections

```
--fpath-parts=<path_to>/labels/building_parts_list.json
--fpath-property-groups=<path_to>/labels/building_properties_categorized.json
```

Building parts
```
{"parts": ["window","door","garage","disaster_mitigation"]}
```

Building properties
```
{"completeness": [ "complete", "incomplete" ], "security": [ "unsecured", "secured" ] ....}
```
