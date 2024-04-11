#  Housing Passports pre processing
To prepare the data, we utilized two packages.

## Packages
The following packages are open-source:

- [geokit](https://github.com/developmentseed/geokit): A utility written in various languages containing a collection of versatile scripts.
- [spherical2images](https://github.com/developmentseed/spherical2images): A package designed to extract sides of a 360-degree image.


## Running Bash

```shell

bash pre_processing.sh
```

### Script Explanation

1. Downloading Points: We specify the bounding box (bbox), filter by organization ID, and set the date to retrieve 
our points. The script fetches points along with their metadata.  For further details, refer to: 
   [get-mapillary-points](https://developmentseed.org/geokit-doc-seed/usage/get-mapillary-points/)

```shell

$geokitdocker get_mapillary_points \
   --input_aoi=-61.493225,15.204024,-61.232986,15.642874 \
   --organization_ids=276431331814934 \
   --timestamp_from=1672531200000 \
   --only_pano \
   --output_file_point=${outputDir}/mapillary_points_panoramic__pano.geojson \
   --output_file_sequence=${outputDir}/mapillary_sequences_panoramic__pano.geojson
```

2. Obtaining Images for Each Point: Using the list of points, we initiate image downloads and store them in 
output_images_path. The script handles the extraction of sides from a 360-degree image using cube_sides.  Refer to 
   the following for more details: [clip-pano-images](https://github.com/developmentseed/spherical2images?tab=readme-ov-file#clip-pano-images-into-left-an-right-side)

```shell

$spherical2imagesdocker clip_mapillary_pano \
  --input_file_points=${outputDir}/mapillary_points_panoramic__pano__pano.geojson \
  --image_clip_size=1024 \
  --output_file_points=${outputDir}/mapillary_points_panoramic_process_new.geojson \
  --output_images_path=${outputDir}/images_new \
  --cube_sides=right,left
```

## coco format
The annotation process was conducted using the [CVAT](https://github.com/opencv/cvat) tool from OpenCV. This tool 
provides the option to download data in various formats, one of which is [COCO format](https://opencv.github.io/cvat/docs/manual/advanced/formats/format-coco/).






