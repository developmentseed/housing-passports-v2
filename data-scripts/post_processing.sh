#!/usr/bin/env bash
set -e

export AWS_PROFILE=

dataOut=data

geokitpy="docker run --rm -v ${PWD}:/mnt/data developmentseed/geokit:python.latest"

# download data
aws s3 cp s3://hp-images-v2/mapillary_files/map_points__pano_clip.geojson $dataOut/map_points__pano_clip.geojson


# convert xml to csv
$geokitpy cvat xml2csv \
  --xml_file=$dataOut/annotations.xml \
  --csv_file=$dataOut/annotations.csv \
  --full=True


attach_cvat_data \
  $dataOut/annotations.csv \
  $dataOut/map_points__pano_clip.geojson \
  $dataOut/annotation_merge.geojson \
  $dataOut/annotation_merge_format.csv

