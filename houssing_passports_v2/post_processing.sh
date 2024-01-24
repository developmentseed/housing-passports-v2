#!/usr/bin/env bash
set -e

export AWS_PROFILE=yunica-hp

dataOut=data
dataPrepared=$dataOut/files_for_db
shpOut=$dataPrepared/shp_building

mkdir -p $shpOut

geokitpy="docker run --rm -v ${PWD}:/mnt/data developmentseed/geokit:python.latest"
hpdev="docker run --rm -v ${PWD}:/mnt developmentseed/hpdev:v2"

# ###################
# download data
# ###################

#aws s3 cp s3://hp-images-v2/mapillary_files/map_points__pano_clip.geojson $dataOut/map_points__pano_clip.geojson
#aws s3 cp s3://hp-deliverables-v2/xml_format/parts_left.xml $dataOut/parts.xml
#aws s3 cp s3://hp-deliverables-v2/xml_format/properties_left.xml $dataOut/properties.xml
#aws s3 cp s3://hp-images-v2/mapillary_files/bldgs_combined.gpkg $dataOut/bldgs_combined.gpkg
# ###################
# sync images
# ###################
#aws s3 sync s3://hp-images-v2/mapillary_images/ $dataOut/images
# ###################
# convert xml to csv
# ###################

#$geokitpy cvat xml2csv \
#  --xml_file=$dataOut/properties.xml \
#  --csv_file=$dataOut/properties.csv \
#  --full=True
#
#$geokitpy cvat xml2csv \
#  --xml_file=$dataOut/parts.xml \
#  --csv_file=$dataOut/parts.csv \
#  --full=True



# ###################
# process data
# ###################

$hpdev attach_data \
  --annotation_properties_csv=$dataOut/properties.csv \
  --annotation_parts_csv=$dataOut/parts.csv \
  --original_geojson=$dataOut/map_points__pano_clip.geojson \
  --gpkg_buildings_file=$dataOut/bldgs_combined.gpkg \
  --prefix_path_images=$dataOut/images \
  --shp_buildings_file=$shpOut/shp_building.shp \
  --geojson_merge_output=$dataPrepared/annotation_merge.geojson \
  --csv_output_trajectory=$dataPrepared/trajectory.csv \
  --props_inference_file=$dataPrepared/props_inference_file.json \
  --props_map_file=$dataPrepared/props_map_file.pbtxt \
  --parts_inference_file=$dataPrepared/parts_inference_file.json \
  --parts_map_file=$dataPrepared/parts_map_file.pbtxt \
  --props_keys_file=$dataPrepared/properties_key.json \
  --part_keys_file=$dataPrepared/parts_key.json

#aws s3 sync $dataPrepared/ s3://hp-images-v2/files_for_db
