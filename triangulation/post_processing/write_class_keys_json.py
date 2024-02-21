"""
To get keys and properties maps so we can distll the detections into single attribute per category

author: @developmentseed

write_class_keys_json.py
~~~
usage:
      python3 write_class_keys_json.py
"""
import os
from os import path as op

import tensorflow as tf

import json
from object_detection.utils import label_map_util


def get_class_map(parts_pbtxt, prop_pbtxt, parts_cls_no, prop_cls_no):
    """ get the attributes of parts and properties

    -----
    Args:
        parts_pbtxt:builiding parts pbtxt file;
        prop_pbtxt: building properties pbtxt file;
        parts_cls_no: number of classes in parts, e.g. 4;
        prop_cls_no: number of classes in properties, e.g. 20;

    Returns:
         (None): json files store parts and properties as meta data
    """
    label_map_util.tf = tf.compat.v1
    tf.gfile = tf.io.gfile
    map_parts = label_map_util.create_category_index_from_labelmap(
        parts_pbtxt, use_display_name=True)
    map_properties = label_map_util.create_category_index_from_labelmap(
        prop_pbtxt, use_display_name=True)
    print(map_parts, map_properties)

    parts = [map_parts[int(class_id)]['name'] for class_id
             in range(1, int(parts_cls_no)+1)]
    properties = [map_properties[int(class_id_)]['name'] for class_id_
             in range(1, int(prop_cls_no)+1)]

    part_dict = dict(parts = parts)
    prop_dict = dict(properties=properties)
    with open(f'{data_dir}/parts_key.json', 'w') as parts_j:
        json.dump(part_dict, parts_j)
        print(f'write class json of parts to {data_dir}')

    with open(f'{data_dir}/properties_key.json', 'w') as prop_j:
        json.dump(prop_dict, prop_j)
        print(f'write class json of property to {data_dir}')


data_dir = "post_processing_data"

parts_map_fpath = f'{data_dir}/building_parts.pbtxt'
props_map_fpath = f'{data_dir}/building_properties-padang.pbtxt'

get_class_map(parts_map_fpath, props_map_fpath, 4, 23)
