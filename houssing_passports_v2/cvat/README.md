## context
The CLI is responsible for merging raw data and preparing it for the execution of the triangulation algorithm located in the [repository](https://github.com/developmentseed/housing-passports)

Once the results are generated when the script is executed ([post_processing.sh](https://github.com/developmentseed/housing-passports-v2/blob/feat/post-processing/houssing_passports_v2/post_processing.sh)), a [files_for_db](https://github.com/developmentseed/housing-passports-v2/blob/f1284a73bb390513fb79d984270c653a6f8e5e3b/houssing_passports_v2/post_processing.sh#L7) folder is created, 
it is the folder that is associated in the following script ([db_compilation.sh](https://github.com/developmentseed/housing-passports/blob/99785f3c4ce635bd9e313aad5294e795248801b3/db_compilation.sh#L3))

## attach_data
This function is in charge of preparing the data. For this, it requires data in specific formats.

```python
"""
   Parameters:
   
    input files
    - annotation_properties_csv (str): Path CSV file containing annotation properties.
    - annotation_parts_csv (str): Path CSV file containing annotation parts.
    - original_geojson (str): Path GeoJSON points file.
    - gpkg_buildings_file (str): Path GeoPackage file with building data.
    - prefix_path_images (str): Prefix path for images.
    
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
### input files

 - **annotation_properties_csv** : Each element is a box that contains the attributes of the buildings properties. 
   - *img_id* : The index in lexical order of images
   - *img_width* : Image width in pixels.
   - *img_height* : Image height in pixels.
   - *img_path* : Relative path to the image file within the dataset.
   - *img_name* : Name of the image file.
   - *box_label* : Associated label
   - *box_occluded* : Indicates whether the object within the bounding box is occluded.
   - *box_xtl* : Top-left corner X coordinate.
   - *box_ytl* : Top-left corner Y coordinate.
   - *box_xbr* : Bottom-right corner X coordinate.
   - *box_ybr* : Bottom-right corner Y coordinate.
   - *box_attr_building_condition* : Value of the attribute `building_condition`.
   - *box_attr_building_security* : Value of the attribute `building_security`.
   - *box_attr_building_use* : Value of the attribute `building_use`.
   - *box_attr_building_material* : Value of the attribute `building_material`.
   - *box_attr_building_completeness* : Value of the attribute `building_completeness`.
   
example:

|img_id|img_width|img_height|img_path|img_name|box_label|box_occluded|box_xtl|box_ytl|box_xbr|box_ybr|box_attr_building_condition|box_attr_building_security|box_attr_building_use|box_attr_building_material|box_attr_building_completeness|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|6|1024|1024|10mYOMtrCj5JK6xSQPHfWX/left|170212829443711_left.jpg|building_properties|0|804.00|303.40|1024.00|626.30|poor|secured|residential|plaster|complete|
|8|1024|1024|10mYOMtrCj5JK6xSQPHfWX/left|200450689554449_left.jpg|building_properties|0|923.49|467.84|1024.00|557.77|complete|mix-other-unclear|commercial|unsecured|fair|


- **annotation_parts_csv** : Each element is a box that contains the attributes of the buildings parts.
  - *img_id* : The index in lexical order of images
  - *img_width* : Image width in pixels.
  - *img_height* : Image height in pixels.
  - *img_path* : Relative path to the image file within the dataset.
  - *img_name* : Name of the image file.
  - *box_label* : Associated label
  - *box_occluded* : Indicates whether the object within the bounding box is occluded.
  - *box_xtl* : Top-left corner X coordinate.
  - *box_ytl* : Top-left corner Y coordinate.
  - *box_xbr* : Bottom-right corner X coordinate.
  - *box_ybr* : Bottom-right corner Y coordinate.
 
    example:

| img_id | img_width | img_height | img_path | img_name | box_label | box_occluded | box_xtl | box_ytl | box_xbr | box_ybr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 1024 | 1024 | 10mYOMtrCj5JK6xSQPHfWX/left | 224506170271277_left.jpg | door | 0 | 508.40 | 394.85 | 614.49 | 602.05 | 
| 11 | 1024 | 1024 | 10mYOMtrCj5JK6xSQPHfWX/left | 224506170271277_left.jpg | window | 0 | 160.39 | 62.42 | 387.60 | 186.70 |

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
- **gpkg_buildings_file** : Contains the original polygons in geopackage format, attributes are not evaluated.
- **prefix_path_images** : It is the relative path of the images.
