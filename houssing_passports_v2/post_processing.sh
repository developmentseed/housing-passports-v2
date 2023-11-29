#!/usr/bin/env bash
set -e

export AWS_PROFILE=yunica-hp

dataOut=data
dataPrepared=$dataOut/files_for_db
shpOut=$dataPrepared/shp_building

mkdir -p $shpOut

#geokitpy="docker run --rm -v ${PWD}:/mnt/data developmentseed/geokit:python.latest"

# download data
#aws s3 cp s3://hp-images-v2/mapillary_files/map_points__pano_clip.geojson $dataOut/map_points__pano_clip.geojson
#aws s3 cp s3://hp-deliverables-v2/parts_left.xml $dataOut/parts.xml
#aws s3 cp s3://hp-deliverables-v2/properties_left.xml $dataOut/properties.xml
#aws s3 cp s3://hp-images-v2/mapillary_files/bldgs_combined.gpkg $dataOut/bldgs_combined.gpkg
#
## convert xml to csv
#$geokitpy cvat xml2csv \
#  --xml_file=$dataOut/properties.xml \
#  --csv_file=$dataOut/properties.csv \
#  --full=True
#
#$geokitpy cvat xml2csv \
#  --xml_file=$dataOut/parts.xml \
#  --csv_file=$dataOut/parts.csv \
#  --full=True

attach_cvat_data \
  $dataOut/properties.csv \
  $dataOut/parts.csv \
  $dataOut/map_points__pano_clip.geojson \
  $dataOut/bldgs_combined.gpkg \
  $dataPrepared/annotation_merge.geojson \
  $shpOut/shp_building.shp \
  $dataPrepared/trajectory.csv \
  $dataPrepared/props_inference_file.json \
  $dataPrepared/props_map_file.pbtxt \
  $dataPrepared/parts_inference_file.json \
  $dataPrepared/parts_map_file.pbtxt \
  /Users/juniorflores/Developer/housing-passports-v2/houssing_passports_v2/data/images \
  $dataPrepared/properties_key.json \
  $dataPrepared/parts_key.json

#aws s3 sync $dataPrepared s3://hp-images-v2/data_prepared/
