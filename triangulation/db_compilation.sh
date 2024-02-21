#!/usr/bin/bash
set -x

inputDir=files_for_db
outputDir=triangulation_results
COUNTRY=dominica
PG_CONNECTION=postgresql://postgres:1234@hpdb:5432/db_passport
neighborhoods=(n1 n2 n3 n4 n5 n6 n7 n8 n9 n10)
# neighborhoods=(n1)

export TF_CPP_MIN_LOG_LEVEL=2
export CUDA_VISIBLE_DEVICES=""
mkdir -p $outputDir

# ##############################################################
# ## Dowload files input files from s3 
# ##############################################################
#Change the s3 names of the file paths to download the building footprint and inference results.
aws s3 sync s3://hp-deliverables-v2/files_for_db_comp_r1_l3/ ${inputDir}/
aws s3 sync s3://hp-deliverables-v2/dominica_buildings/building_simplified_by_aoi/ $inputDir/dominica_buildings/

# ##############################################################
# ## Import Files into DB
# ##############################################################

passport_db_export ${PG_CONNECTION} \
  --trajectory-fpath=$inputDir/trajectory.csv \
  --geomfile-fpath=$inputDir/dominica_buildings/building_simplified.shp \
  --parts-inference-fpath=$inputDir/parts_inference_file.json \
  --props-inference-fpath=$inputDir/props_inference_file.json \
  --parts-map-fpath=$inputDir/parts_map_file.pbtxt \
  --props-map-fpath=$inputDir/props_map_file.pbtxt

# ##############################################################
# ## Linking detections to buildings in database
# ##############################################################

for neighborhood in "${neighborhoods[@]}"
do
    echo 'passport_link_db_detections for neighborhood...' $neighborhood
    passport_link_db_detections \
        ${PG_CONNECTION} \
        --neighborhood=${neighborhood}
done


###############################################################
### Distill many detections into single attribute per category
### This sets attributes according to highest total confidence (for building properties) or max number observed instances (building parts)
###############################################################

for neighborhood in "${neighborhoods[@]}"
do
    echo 'passport_distill_metadata for neighborhood...' $neighborhood
    passport_distill_metadata \
        ${PG_CONNECTION} \
        --fpath-parts=$inputDir/parts_key.json \
        --fpath-property-groups=$inputDir/properties_key.json \
        --neighborhood=${neighborhood}
done

###############################################################
### Generate a geojson file containing linestrings for each ML detections for testing
###############################################################

mkdir -p $outputDir/detections_ray
set +x
for neighborhood in "${neighborhoods[@]}"
do
    echo 'Generate a geojson file containing linestrings for each ML detections for neighborhood...' $neighborhood
    passport_detection_export ${PG_CONNECTION} \
        --neighborhood=${neighborhood} \
        --det_class=complete \
        --det_class=incomplete \
        --det_class=poor \
        --det_class=fair \
        --det_class=good \
        --det_class=mix-other-unclear \
        --det_class=brick_or_cement-concrete_block \
        --det_class=wood_polished \
        --det_class=stone_with_mud-ashlar_with_lime_or_cement \
        --det_class=corrugated_metal \
        --det_class=wood_crude-plank \
        --det_class=container-trailer \
        --det_class=plaster \
        --det_class=adobe \
        --det_class=secured \
        --det_class=unsecured \
        --det_class=residential \
        --det_class=critical_infrastructure \
        --det_class=mixed \
        --det_class=commercial \
        --linked-dets-only=True \
        --save-fpath=$outputDir/detections_ray/${neighborhood}_lines_ok.geojson
done
python post_processing/merge_geojson.py $outputDir/detections_ray/ $outputDir/${COUNTRY}_ray_lines.shp

# ###############################################################
# ### Get full db backup
# ###############################################################

pg_dump ${PG_CONNECTION}  | gzip -9 > $outputDir/${COUNTRY}_ok.sql.gz

# ###############################################################
# ###  Get the buildings geojson with predictions
# ###############################################################
mkdir -p $outputDir/buildings/
for neighborhood in "${neighborhoods[@]}"
do
    echo 'Export buildings' $neighborhood
    python post_processing/create_geojson_buildings.py ${PG_CONNECTION} ${neighborhood} $outputDir/buildings/${neighborhood}_ok.geojson
done
python post_processing/merge_geojson.py $outputDir/buildings/ $outputDir/${COUNTRY}_buildings.shp

## Set the s3 path to upload the results
aws s3 sync $outputDir/ s3://hp-deliverables-v2/$outputDir/
