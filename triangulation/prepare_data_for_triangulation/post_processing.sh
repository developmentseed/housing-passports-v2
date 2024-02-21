#!/usr/bin/env bash
set -e

dataOut=data
dataPrepared=$dataOut/files_for_db
shpOut=$dataPrepared/shp_building

mkdir -p $shpOut

#hpdev="docker run --rm -v ${PWD}:/mnt developmentseed/hpdev:v2"

# ###################
# download data
# ###################
#aws s3 cp s3://hp-deliverables-v2/dominica_predicitions_with_scores_extended_det50k_classifier_fixed_no_aug/all_predictions_with_scores.csv $dataOut/all_predictions_with_scores.csv
#aws s3 cp s3://hp-images-v2/mapillary_files/mapillary_points_panoramic_all.geojson  $dataOut/mapillary_points_panoramic_all.geojson
#aws s3 cp s3://hp-images-v2/mapillary_files/bldgs_buffer_DOM_3.gpkg $dataOut/bldgs_buffer_DOM_3.gpkg

# ###################
# sync images
# ###################

#aws s3 sync s3://hp-images-v2/mapillary_images_new/ $dataOut/mapillary_images_new

# ###################
# process data
# ###################

attach_data \
  --predictions_csv=$dataOut/all_predictions_with_scores.csv \
  --original_geojson=$dataOut/mapillary_points_panoramic_all.geojson \
  --gpkg_buildings_file=$dataOut/bldgs_buffer_DOM_3.gpkg \
  --prefix_path_images=$dataOut/mapillary_images_new \
  --neighborhood=$dataOut/neighborhood.geojson \
  --shp_buildings_file=$shpOut/shp_building.shp \
  --geojson_merge_output=$dataPrepared/annotation_merge.geojson \
  --csv_output_trajectory=$dataPrepared/trajectory.csv \
  --props_inference_file=$dataPrepared/props_inference_file.json \
  --props_map_file=$dataPrepared/props_map_file.pbtxt \
  --parts_inference_file=$dataPrepared/parts_inference_file.json \
  --parts_map_file=$dataPrepared/parts_map_file.pbtxt \
  --props_keys_file=$dataPrepared/properties_key.json \
  --part_keys_file=$dataPrepared/parts_key.json

#aws s3 sync $dataPrepared/ s3://hp-deliverables-v2/files_for_db_comp_r1_l3_new

