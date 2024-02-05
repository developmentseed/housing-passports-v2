#!/usr/bin/env bash
set -e

export AWS_PROFILE=yunica-hp

dataOut=data
dataPrepared=$dataOut/files_for_db
shpOut=$dataPrepared/shp_building

mkdir -p $shpOut

#hpdev="docker run --rm -v ${PWD}:/mnt developmentseed/hpdev:v2"

# ###################
# download data
# ###################
#aws s3 cp s3://hp-deliverables-v2/dominica_predicitions_with_scores/all_predictions_with_scores.csv  $dataOut/all_predictions.csv
#aws s3 cp s3://hp-images-v2/mapillary_files/s3://hp-images-v2/mapillary_files/new_mapillary_points_panoramic_process_update.geojson $dataOut/new_mapillary_points_panoramic_process_update.geojson
#aws s3 cp s3://hp-images-v2/mapillary_files/bldgs_combined.gpkg $dataOut/bldgs_combined.gpkg

# ###################
# sync images
# ###################

#aws s3 sync s3://hp-images-v2/mapillary_images_new/ $dataOut/mapillary_images_new

# ###################
# process data
# ###################

attach_data \
  --predictions_csv=$dataOut/all_predictions_with_scores.csv \
  --original_geojson=$dataOut/new_mapillary_points_panoramic_process_update.geojson \
  --gpkg_buildings_file=$dataOut/bldgs_combined.gpkg \
  --prefix_path_images=$dataOut/mapillary_images_new \
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
