# Housing Passports v2 Data Preparation

This package prepares data from inferences into a format understandable by the triangulation algorithm.


## Running the Script

### Build Docker Image

Run the following command to build the Docker image:

```shell

docker-compose build   

```

### Run

Prepare files for db_compilation, run post_processing.sh:

```shell
bash post_processing.sh

```

## Input Format

The CLI is responsible for merging raw data and preparing it for the execution of the triangulation algorithm located in the [repository](https://github.com/developmentseed/housing-passports)

Once the results are generated when the script is executed ([post_processing.sh](https://github.com/developmentseed/housing-passports-v2/blob/feat/post-processing/houssing_passports_v2/post_processing.sh)), a [files_for_db](https://github.com/developmentseed/housing-passports-v2/blob/f1284a73bb390513fb79d984270c653a6f8e5e3b/houssing_passports_v2/post_processing.sh#L7) folder is created, 
it is the folder that is associated in the following script ([db_compilation.sh](https://github.com/developmentseed/housing-passports/blob/99785f3c4ce635bd9e313aad5294e795248801b3/db_compilation.sh#L3))

### attach_data
This function is in charge of preparing the data. For this, it requires data in specific formats.


```python
"""
   Parameters:
   
    input files
    - predictions_csv (str): Path CSV file containing predictions csv.
    - original_geojson (str): Path GeoJSON points file.
    - gpkg_buildings_file (str): Path GeoPackage file with building data.
    - prefix_path_images (str): Prefix path for images.
    - neighborhood (str): Path GeoJSON boundary file
    output files
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

```
### parametros

 - **predictions_csv** : Each element is a box that contains the attributes of the buildings properties. 

    - *Unnamed:*  The index of the row in lexical order.
    - *image_name:*  Path and name of the image file.
    - *boxes:*  A list of bounding box coordinates represented as - *floating-point values.
    - *box_scores:*  The score associated with the bounding box/row.
    - *complete:*  A string indicating completeness.
    - *condition:*  A string indicating the condition.
    - *material:*  A string indicating the material.
    - *security:*  A string indicating the security level.
    - *use:*  A string indicating the use or purpose.
    - *image_name_clip:*  Path and name of the clipped image file.
    - *boxes_float:*  A list of bounding box coordinates represented as floating-point values.
    - *boxes_int:*  A list of bounding box coordinates represented as integer values.

example:


|Unnamed|image_name|boxes|box_scores|complete|condition|material|security|use|image_name_clip|boxes_float|boxes_int|
|---|---|---|---|---|---|---|---|---|---|---|---|
|0|l1bXKBqgf2ZizCoyxpm9SR/left/640350998183120_left.jpg|"[805.157958984375, 0.0, 1024.0, 682.0144653320312]"|0.895|incomplete|good|plaster|unsecured|residential|l1bXKBqgf2ZizCoyxpm9SR/left/640350998183120_left.jpg|"[805.157958984375, 0.0, 1024.0, 682.0144653320312]"|"[805, 0, 1024, 682]"|
|1|l1bXKBqgf2ZizCoyxpm9SR/left/640350998183120_left.jpg|"[2.8056640625, 404.6286926269531, 332.5999450683594, 543.6171875]"|0.535|complete|fair|plaster|secured|residential|l1bXKBqgf2ZizCoyxpm9SR/left/640350998183120_left_1.jpg|"[2.8056640625, 404.6286926269531, 332.5999450683594, 543.6171875]"|"[2, 404, 332, 543]"|

 
- **original_geojson** : Each element is a point from mapillary data.
  - *captured_at* : Timestamp in ms since epoch.
  - *compass_angle* : The compass angle of the image.
  - *id* : Image id.
  - *is_pano* : If it is a panoramic image.
  - *organization_id* : ID of the organization this image belongs to.
  - *sequence_id* : ID of the sequence this image belongs to.
  - *image_path* : Image path in aws s3, from this path it is determined whether the image is to the right or to the left.

    example:

```json
{
   "type":"Feature",
   "geometry":{
      "type":"Point",
      "coordinates":[
         -61.46082937717438,
         15.583129017592881
      ]
   },
   "properties":{
      "captured_at":1692223800000,
      "compass_angle":329.562,
      "id":627834716082798,
      "is_pano":true,
      "organization_id":276431331814934,
      "sequence_id":"SG4gUpQDdl1HvxCkMzErFq",
      "image_path":"s3://hp-images-v2/mapillary_images/SG4gUpQDdl1HvxCkMzErFq/right/627834716082798_right.jpg"
   }
}
```
- **gpkg_buildings_file** : Contains the original footprints in geopackage format, attributes are not evaluated.
- **prefix_path_images** : It is the relative path of the images.

- **neighborhood** : Contains the geo boundaries of neighborhood, also each feature has `neighborhood` field.

### output files

- **shp_buildings_file** : Contains the footprints in shapely format, with an additional attribute `neighborho`.

- **geojson_merge_output** : Each element is a point from mapillary data that contains the grouped detections.
  - *box* : contains a list of all detections that belong to the point.
  
    example:

```json
{
   "type":"Feature",
   "geometry":{
      "type":"Point",
      "coordinates":[
         -61.46082937717438,
         15.583129017592881
      ]
   },
   "properties":{
      "captured_at":1692223800000,
      "compass_angle":329.562,
      "id":627834716082798,
      "is_pano":true,
      "organization_id":276431331814934,
      "sequence_id":"SG4gUpQDdl1HvxCkMzErFq",
      "image_path":"s3://hp-images-v2/mapillary_images/SG4gUpQDdl1HvxCkMzErFq/left/627834716082798_left.jpg",
      "compass_angle_fix":120.44,
      "box":[
         {
            "img_id":"6842",
            "img_width":"1024",
            "img_height":"1024",
            "img_path":"SG4gUpQDdl1HvxCkMzErFq/left",
            "img_name":"627834716082798_left.jpg",
            "box_label":"building_properties",
            "box_occluded":"0",
            "box_xtl":"123.84",
            "box_ytl":"399.83",
            "box_xbr":"501.77",
            "box_ybr":"689.10",
            "box_attr_building_condition":"residential",
            "box_attr_building_security":"complete",
            "box_attr_building_use":"wood_polished",
            "box_attr_building_material":"unsecured",
            "box_attr_building_completeness":"fair"
         },
         ...
      ]
   }
}
```

- **csv_output_trajectory** : GPS trajectory info for each image.
  - *heading[deg]* : Compass heading of point.
  - *image_fname* : Image file name.
  - *frame* : Frame number of the image.
  - *latitude[deg]* : Longitude of the point.
  - *longitude[deg]* : Latitude of the point.
  - *cam* : Camera number.
  - *neighborhood* : Neighborhood where frame was taken.
  - *subfolder* : Relative path to the image file within the dataset.
 
  example:

|heading[deg]|image_fname|frame|latitude[deg]|longitude[deg]|cam|neighborhood|subfolder|
|---|---|---|---|---|---|---|---|
|47.32|267316452731807_left.jpg|267316452731807_left|15.469439229239484|-61.45654857158661|1|n1|data/images/CXIswiV1efalvHrFonDW23/left|
|76.57|201534059574615_left.jpg|201534059574615_left|15.483594425549313|-61.462910771369934|1|n1|data/images/CXIswiV1efalvHrFonDW23/left|

- **props_inference_file** : List of detections of building properties.

    example:

```json

{
   "detection_scores":[
      1,
      1,
      ...
   ],
   "detection_classes":[
      18,
      13,
      ....
   ],
   "detection_boxes":[
      [
         0.781,
         0.517,
         0.954,
         0.633
      ],
      ...
   ],
   "image_fname":"267316452731807_left.jpg",
   "subfolder":"data/images/CXIswiV1efalvHrFonDW23/left",
   "cam":1,
   "frame":"267316452731807_left",
   "neighborhood":"n1"
}

```

- **props_map_file** : PBTXT file mapping building properties.

    example:

```text

item {
  id: 1
  name: 'brick_or_cement-concrete_block'
}
...

```

- **parts_inference_file** : List of detections of building parts.

    example:

```json

{
   "detection_scores":[
      1,
      ...
   ],
   "detection_classes":[
      1,
      ...
   ],
   "detection_boxes":[
      [
         0.802,
         0.552,
         0.833,
         0.584
      ],
      ...
   ],
   "image_fname":"267316452731807_left.jpg",
   "subfolder":"data/images/CXIswiV1efalvHrFonDW23/left",
   "cam":1,
   "frame":"267316452731807_left",
   "neighborhood":"n1"
}

```

- **parts_map_file** : PBTXT file mapping building parts.

    example:

```text

item {
  id: 1
  name: 'window'
}
...

```

- **props_keys_file** : Json building properties.

    example:

```json

{
  "materials":[
     "brick_or_cement-concrete_block",
     "plaster",
     "wood_polished",
     "wood_crude-plank",
     ....
  ],
  "use":[
     "residential",
     "mixed",
     ...
  ],
  ...
}

```

- **part_keys_file** : Json building parts.

    example:

```json

{
  "parts":[
     "window",
     "door",
     "garage",
     "disaster_mitigation"
  ]
}

```
