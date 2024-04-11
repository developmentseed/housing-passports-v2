# Processing files to attach predictions to building footprints

This documentation guides you through the process of inserting essential data, including buildings, images, and detections, into the Housing Passport database. Follow these steps for seamless integration and efficient management of data.

## 1. Build the container
To build the container, run the following command. Everything will be installed within the Docker container.

```bash
cd housing-passport/
docker-container build
```

## 2. Dump Data into Database

Execute the following command to start up the database:

```bash
docker-container up hpdb -d
```

## 3. Launch the development container to interact with the database
To interact with the database, commence the container by executing the following command:

```bash
docker-container run hpdev bash
```

Once inside the container, run the bash script `./db_compilation.sh` This script will create everything required for running the CLI sequentially in order.

Before running the script, ensure that you update the S3 bucket location to fetch the necessary files, and also results will be uploaded to the same bucket.

## Additional Details and File Formats

Here are further details and file formats required for the successful execution of the process:

### File Formats

#### Trajectory File Format
Specify the trajectory file format using the following parameter:

```bash
--trajectory-fpath=<path_to>/trajectory/padang.csv
```

Example CSV format:
- Padang:
```csv
heading[deg],image_fname,frame,latitude[deg],longitude[deg],cam,neighborhood,subfolder
238.81604587884,ladybug_14062044_20190628_141526_Cube_000000_Cam1_879_090-0881.jpg,ladybug_14062044_20190628_141526_Cube_000000,-0.937739981443431,100.377668449777,"1",padang,PADANG_01
...
```
- Dominica:
```
heading[deg],image_fname,frame,latitude[deg],longitude[deg],cam,neighborhood,subfolder
157.99,1217711312238013_right.jpg,1217711312238013_right,15.58436914933641,-61.463109254837036,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
84.05,810147150770972_right.jpg,810147150770972_right,15.58661170189599,-61.46408021450043,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
85.27,275015961941994_right.jpg,275015961941994_right,15.587045741498912,-61.46405875682831,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
170.56,675728221118444_right.jpg,675728221118444_right,15.584591338816324,-61.463865637779236,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
169.45,1427673917804476_right.jpg,1427673917804476_right,15.584612007592938,-61.46399438381195,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
138.85,324733489975429_right.jpg,324733489975429_right,15.581310144161336,-61.45956873893738,1,n,data/mapillary_images_new/xJz3hlTg4y57OHWjoiU1Xu/right
120.73,284122827588790_right.jpg,284122827588790_right,15.582157575831715,-61.46030902862549,1,n,data/mapillary_images_new/xJz3hlTg4y57OHWjoiU1Xu/right
160.49,981670949715273_right.jpg,981670949715273_right,15.583743917184762,-61.461424827575684,1,n,data/mapillary_images_new/SG4gUpQDdl1HvxCkMzErFq/right
2
```

Where: 
```
heading[deg]: Compass angle
```

#### Rooftop Shapefile Format
Specify the rooftop shapefile format using the following parameter:

```bash
--geomfile-fpath=<path_to>/rooftop/padang.shp
```

Ensure the building footprints metadata includes a `neighborhood` column.

#### Inference Detection File Format
Specify the inference detection file formats using the following parameters:
```bash
--props-inference-fpath=<path_to>/prediction/prediction_filtered_properties.json
--parts-inference-fpath=<path_to>/prediction/prediction_filtered_parts.json
```

Example JSON format:
```json
[  
  {
    "detection_scores": [
      0.9609,
      0.9609,
      0.9609,
      0.9609,
      0.9609
    ],
    "detection_classes": [
      1,
      4,
      19,
      14,
      15
    ],
    "detection_boxes": [
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ],
      [
        0.001611,
        0.381519,
      0.9609
    ],
    "detection_classes": [
      1,
      4,
      19,
      14,
      15
    ],
    "detection_boxes": [
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ],
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ],
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ],
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ],
      [
        0.001611,
        0.381519,
        0.198094,
        0.628517
      ]
    ],
    "image_fname": "324733489975429_right.jpg",
    "subfolder": "data/mapillary_images_new/xJz3hlTg4y57OHWjoiU1Xu/right",
    "cam": 1,
    "frame": "324733489975429_right",
    "neighborhood": "n8"
  }
]
```

Ensure image filenames are formatted appropriately.

### PBtxt Format

#### Building Parts PBtxt Format
Specify the building parts PBtxt format using the following parameter:
```bash
--parts-map-fpath=<path_to>/labels/building_parts.pbtxt
```

Example PBtxt format:
```protobuf
item {
  id: 1
  name: 'window'
}
item {
  id: 2
  name: 'door'
}
...
```

#### Building Properties PBtxt Format
Specify the building properties PBtxt format using the following parameter:
```bash
--props-map-fpath=<path_to>/labels/building_properties.pbtxt
```

Example PBtxt format:
```protobuf
item {
  id: 1
  name: 'brick_or_cement-concrete_block'
}
item {
  id: 2
  name: 'plaster'
}
...
```

### Filter Format for Distill Detections

Specify the filter format for distilling detections using the following parameters:
```bash
--fpath-parts=<path_to>/labels/building_parts_list.json
--fpath-property-groups=<path_to>/labels/building_properties_categorized.json
```

Example filter format:
```json
{
  "parts": [
    "window",
    "door",
    "garage",
    "disaster_mitigation"
  ]
}
```

```json
{
  "complete": [
    "complete",
    "incomplete"
  ],
  "condition": [
    "poor",
    "fair",
    "good"
  ],
  "material": [
    "mix-other-unclear",
    "brick_or_cement-concrete_block",
    "wood_polished",
    "stone_with_mud-ashlar_with_lime_or_cement",
    "corrugated_metal",
    "wood_crude-plank",
    "container-trailer",
    "plaster",
    "adobe"
  ],
  "security": [
    "secured",
    "unsecured"
  ],
  "use": [
    "residential",
    "critical_infrastructure",
    "mixed",
    "commercial"
  ]
}

```

These detailed instructions and file formats ensure a smooth insertion of relevant information into the Housing Passport database, enhancing the overall efficiency of data management and retrieval.


## Hardware requirements:

For optimal performance, it is recommended to use configurations such as xlarge, 2xlarge, or 4xlarge. Due to the resource-intensive nature of database processing, we have developed a script to customize the database container, enhancing the processing speed for a more efficient operation. The script, [server_config.sh](dockerPG/config/server_config.sh), will be executed automatically once you start up the DB container with the environment variable: MACHINE_TYPE: 'xlarge'.