"""
Code to export a TF model created with the Object Detection API. The exported
model can then be packaged into a TF Serving image.

Exporting a model from TF's object detection API was surprisingly difficult.
The below code should bridge the gap from the OD API's
`export_inference_graph.py` script and something ready for TF Serving
"""

import tensorflow as tf

# Assuming object detection API is available for use
from object_detection.utils.config_util import create_pipeline_proto_from_configs
from object_detection.utils.config_util import get_configs_from_pipeline_file
import object_detection.exporter

# Configuration for model to be exported
config_pathname = '/Volumes/ext3/Data/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_singlelabel/190628_2200_building_parts/ssd_resnet101_v1_fpn_singlelabel.config'

# Input checkpoint for the model to be exported
# Path to the directory which consists of the saved model on disk (see above)
trained_model_dir = '/Volumes/ext3/Data/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_singlelabel/190628_2200_building_parts/export_obj_det_api'

# Create proto from model confguration
configs = get_configs_from_pipeline_file(config_pathname)
pipeline_proto = create_pipeline_proto_from_configs(configs=configs)

# Read .ckpt and .meta files from model directory
checkpoint = tf.train.get_checkpoint_state(trained_model_dir)
input_checkpoint = "/Volumes/ext3/Data/housing_passports/training_v2/models/ssd_resnet101_v1_fpn_singlelabel/190628_2200_building_parts/export_obj_det_api/model.ckpt"

# Output Directory
output_directory = '/Volumes/ext3/Data/housing_passports/exported_models/ssd_resnet101_v1_fpn_singlelabel/190628_2200_building_parts/001'

# Export model for serving
object_detection.exporter.export_inference_graph(
    input_type='encoded_image_string_tensor',  #XXX use `encoded_image_string_tensor` or `image_tensor` depending on if image is encoded or not. Can also pass tf.Example objects
    pipeline_config=pipeline_proto,
    trained_checkpoint_prefix=input_checkpoint,
    output_directory=output_directory)
