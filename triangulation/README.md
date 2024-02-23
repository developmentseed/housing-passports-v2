#  Housing Passports triangulation algorithm

The Housing Passports project is a collaboration with the World Bank to improve housing resilience.

The WB is interested in detecting specific construction features within geotagged street view imagery. Their goal is to find building features that are potentially dangerous during earthquakes, high winds, floods, etc. A good example is their initial push in Guatemala where they were looking for "soft story" buildings; These are 2+ level structures that have large windows or garage doors on the ground floor -- the large openings correspond to a high risk that the building will collapse and pancake during earthquakes. Other features could include incomplete construction, age of the building, construction material, etc.

Their hope is to detect dangerous features in street view images using ML, extract the specific locations of these features, and then rely on local groups to deploy fixes or improvements.

## Labeling on the Computer Vision Annotation Tool
For more details please read our labeling report or [labeling guide](http://devseed.com/housing-passports-labeling/) by DevSeed Data Team.

<details>


See the [labeling guide](http://devseed.com/housing-passports-labeling/), which contains all example updated.  

In Housing Passports Phase 2 we labeled:

### Building Parts
* window
* door
* garage
* disaster_mitigation

### Building Properties
* material
  * brick_or_cement-concrete_block
  * plaster
  * wood_polished
  * wood_crude-plank
  * adobe
  * corrugated_metal
  * stone_with_mud-ashlar_with_lime_or_cement
  * container-trailer
  * plant_material
  * mix-other-unclear
* completeness
  * complete
  * incomplete
* use
  * residential
  * mixed
  * non_residential
* security
  * unsecured
  * secured
* condition
  * average
  * poor
  * good
* vintage
  * not_defined
  * pre_1940
  * 1941_1974
  * 1975_1999
  * 2000_now

</details>

## Constructing training data

1. Set `label_params` parameters in `config_data.py`. Be sure to specify these properly depending on if you want to create training data for building parts (where there is a single detection per object) or building properties (where there can be multiple building detections per object).
1. Run `convert_cvat_txt.py` to convert XML data from the labeling platform
1. Run `convert_cvat_tfrecords.py` to convert XML data to TFRecords files (for training with TF Object Detection API).



## Training a model

### Runnning Object Detection in KubeFlow

```bash
# Shell script to:
# - download and install KFCTL tool
# - set up and deploy K8s cluster and Kubeflow;
# - using gcloud to grand IAM roles;
# - add GPUs as notepool to train ML models;
chmod +x kubeflow_hp/deploy_kf.sh
bash kubeflow_hp/deploy_kf.sh
```

### Verifying resources
This connects kubectl to your cluster.

```
gcloud container clusters get-credentials ${KF_NAME} --zone ${ZONE} --project ${PROJECT}
kubectl -n kubeflow get all
```

### Launching Kubeflow Pipeline

Then open up the Kubeflow UI by looking in GKE > Services & Ingress. It should be something like `https://kubeflow-app-vX.endpoints.bp-padang.cloud.goog/`. Note that the  take 5-10 minutes to come online _after_ the cluster is completely ready (so be patient if you're getting `This site can’t be reached` or `This site can’t provide a secure connection` messages). Go to the Pipelines tab and upload the .tar.gz file to the Kubeflow Pipelines UI and kick off a run.

Reasonable defaults/examples for pipeline parameters:

| Parameter  | Example |
| ------------- | ------------- |
| pipeline_config_path | `gs://bp-padang/model_dev/model_templates/ssd_resnet101_v1_fpn_multilabel.config` |
| model_dir | `gs://bp-padang/experiments/1` |
| eval_dir | `gs://bp-padang/experiments/1/eval_0` |
| inference_output_directory | `gs://bp-padang/experiments/1/best_eval` |
| num_train_steps | `10000` |
| sample_1_of_n_eval_examples | `1` |
| eval_checkpoint_metric | `loss` |
| metric_objective_type | `min` |
| inference_input_type | `encoded_image_string_tensor` |



### Clean up
```bash
# Delete cluster/resources once finished. You can skip deleting the storage if you want to rerun the same cluster later
kfctl delete -f ${CONFIG_FILE} --delete_storage
```

Read more on how a model performing was evaluated [here](model_evaluation/README.md)

Old workflow showed in the following detail. But from now on please use Kubeflow pipeline.

<details>


Start an AWS GPU instance and specify the user-data file to set up the directory structure. You can also do this through AWS's GUI.
```bash
spot start --user-data aws/user-data
housing-passports/aws/prep_live_instance.sh ${ip}
```

Start ML model training using the proper configuration file and model directory
```bash
cd ~/Builds/tensorflow/models/research/object_detection

PIPELINE_CONFIG_PATH=$BUILDS_DIR/housing-passports/model_pipeline_templates/ssd_resnet101_v1_fpn_multilabel.config
MODEL_DIR=$DATA_DIR/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_multilabel
python model_main.py --pipeline_config_path=${PIPELINE_CONFIG_PATH} --model_dir=${MODEL_DIR} --sample_1_of_n_eval_examples=1 --alsologtostderr
```
</details>

## Constructing TF Serving Image

Make sure to update the tensorflow `models` folder (with git pull) and reinstall the proto buffers if necessary according to: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md

### Creating necessary export files
```bash
cd $BUILDS_DIR
git clone https://github.com/tensorflow/models.git
cd tensorflow/models
~/anaconda3/envs/tensorflow_p36/bin/pip install -e .

cd $BUILDS_DIR/models/research
INPUT_TYPE=encoded_image_string_tensor
PIPELINE_CONFIG_PATH=$EXT_DATA_DIR/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_multilabel/190721_1100_building_properties/ssd_resnet101_v1_fpn_multilabel.config
TRAINED_CKPT_PREFIX=$EXT_DATA_DIR/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_multilabel/190721_1100_building_properties/model.ckpt-10525
EXPORT_DIR=/Volumes/ext3/Data/housing_passports/exported_models/ssd_resnet101_v1_fpn_multilabel/190721_1100_building_properties/

python $BUILDS_DIR/models/research/object_detection/export_inference_graph.py \
    --input_type=${INPUT_TYPE} \
    --pipeline_config_path=${PIPELINE_CONFIG_PATH} \
    --trained_checkpoint_prefix=${TRAINED_CKPT_PREFIX} \
    --output_directory=${EXPORT_DIR}
```

### Prepping directory for copying into TF Serving image
Then rearrange the contents in your `EXPORT_DIR` folder to look like:
```
190721_1100_building_properties/
|--001/
   |--saved_model.pb
   |--variables/
   	  |--variables.data-00000-of-00001
      |--variables.index
```

### Create TF Serving image
Drop the `-gpu` tag suffix if you want to create a CPU version of the image

```bash
cd /Volumes/ext3/Data/housing_passports/exported_models/ssd_resnet101_v1_fpn_multilabel
docker run -d --name serving_base tensorflow/serving:1.13.0-gpu
docker cp 190721_1100_building_properties serving_base:/models/building_properties
docker commit --change "ENV MODEL_NAME building_properties" serving_base developmentseed/building_properties:v1-gpu
docker kill serving_base
docker container prune
docker push developmentseed/building_properties:v1-gpu
```

## Inference w/ TF Serving Image

Please use [Chip n Scale](https://github.com/developmentseed/chip-n-scale-queue-arranger) to deploy model inference.

The actual walkthrough of deploy a housing passports model inference with Chip n Scale please read [this instruction](chip-n-scale-deployment/README.md).

<details>

```bash
# If needed, update AWS credentials
aws configure --profile housing_passports

# Download all data ready for inference (images downsized to 512x512)
aws s3 cp s3://wbg-geography01/GEP/DRONE/ ~/Data/housing_passports/inference --recursive --exclude=* --include='*downsized*' --profile housing_passports

# Run the GPU docker image; Use `building_parts` or `building_properties`
docker run --runtime=nvidia -p 8501:8501 -t developmentseed/building_properties:v1-gpu

# Run predictions for all city subfolders
# Each city (e.g., `LIMA`) contains image subfolders (e.g., `CubeImage_140`, `CubeImage_141`, etc.)
IMAGE_HEAD_DIR=~/Data/housing_passports/inference
for d in $(find $IMAGE_HEAD_DIR -maxdepth 2 -mindepth 2 -type d) ; do
    echo $d
    mkdir $d/preds_properties
    # Use `building_parts` or `building_properties` for prediction image and `preds_parts` or `preds_properties for save directory
    passport_predict $d/downsized http://localhost:8501/v1/models/building_properties:predict --save-directory $d/preds_properties --batch-size 16
done

# Upload predictions back to S3
# Use `preds_parts` or `preds_properties
aws s3 cp ~/Data/housing_passports/inference s3://wbg-geography01/GEP/DRONE/ --recursive --exclude=* --include='*preds_properties*.json' --profile housing_passports
```

</details>

## Compile inference results into PostGRES database

Please use read detailed documentation on how we populate HP PostgreSQL database [here](post_processing/README.md)

<details>





### Insert information into DB

Take a look into [COMPILING_FILE_INTO_DB.md](/COMPILING_FILE_INTO_DB.md)

</details>


### Create geojson map of detections

Generate a geojson file containing linestrings for each ML detections. This is useful for visualizing ML detections against buildings footprints and the car's GPS trajectory.

```bash
COUNTRY=colombia
CITY=CARTAGENA

passport_detection_export \
postgresql://hp:ChangeThePassword@localhost:5432/${COUNTRY} \
--save-fpath=/Volumes/ext3/Data/housing_passports/data/detections/${COUNTRY}/${CITY}_detections.geojson \
--neighborhood=${CITY} \
--det_class=complete --det_class=incomplete \
--linked-dets-only=True
```
