"""
Construct TF Records file from CVAT xml

@author: Development Seed
"""
import io
import os
import os.path as op
from os import makedirs
import hashlib
from pathlib import Path
from os import listdir

from tqdm import tqdm
import boto3
import tensorflow as tf
import PIL
from object_detection.utils import  dataset_util

from utils_convert import (parse_xml_examples, parse_image_filepath_v1,
                           norm_bbox_coord)
from config_data import (DOWNSAMP_IMG_SHP,
                         label_params as LABEL_PARAMS,
                         s3_download_params,
                         label_map_dict_whole_building,
                         whole_building_properties)

def download_img_s3(bucket, s3_prefix, folder, fname, s3_profile, downsized=True):
    """Download image from s3 to local directory

    Parameters
    ----------
    bucket: str
        S3 bucket name
    S3_prefix: str
        S3 prefix/direcotry to image file
    fname: str
        Image file name
    s3_profile:
        S3 profile for the bucket

    Return
    --------
    local_file: str
    path to the saved image on local directory

    """
    dir_add = '-downsized' if downsized else ''
    local_dir = op.join(os.getcwd(), folder+dir_add)

    if not op.isdir(local_dir):
        makedirs(local_dir)

    s3_key = op.join(s3_prefix, folder+dir_add, fname)
    client = boto3.session.Session(profile_name=s3_profile).client('s3')

    local_file= op.join(local_dir, fname)
    client.download_file(bucket, s3_key, local_file)
    return local_file


def dict_to_tf_example(bucket,s3_folder_prefix,s3_profile,
                       data_dict,label_map_dict,
                       multilabel_properties=None, downsized=True,
                       skip_if_missing=True):
    """Convert XML derived dict to tf.Example proto.

    Note: this function normalizes the bounding box coordinates provided by the
    raw data.

    Parameters
    ----------
    data_dict: dict
        PASCAL XML fields for a single image
    label_map_dict: dict
        A map from string label names to integers ids.
    multilabel_properties: None or list of str
        All possible property categories (e.g., 'material', 'completeness',
        etc.). Only use if multilabel objects are desired
    downsized: bool
        Whether to use downsized images.
    skip_if_missing: bool
        Whether to skip this TF example if image is missing.

    Returns
    -------
    example: The converted tf.Example.

    Raises
    ------
    ValueError: if the image pointed to by data['path'] is not a valid JPEG
    """
    _, folder, fname = parse_image_filepath_v1(data_dict['filename'])
    local_fpath = download_img_s3(bucket, s3_folder_prefix, folder, fname, s3_profile, downsized)
    print("Image {} downloaded!".format(local_fpath))
    # if not op.exists(local_fpath) and skip_if_missing:
    #     print(f'Missing image file {local_fpath}. Skipping...')
    #     return None

    # Load image and get bytestring
    with tf.io.gfile.GFile(local_fpath, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format not in ['JPEG', 'jpg', 'JPG']:
        raise ValueError('Image format is not JPEG')

    # print(image)


    # Set some image level properties
    key = hashlib.sha256(encoded_jpg).hexdigest()
    width = int(data_dict['width'])
    height = int(data_dict['height'])
    img_id = int(data_dict['id'])

    # Initialize lists to hold each object annotation in the image
    xmins, ymins, xmaxs, ymaxs = [], [], [], []
    label_int_codes = []
    label_text = []
    difficult = []

    if 'objects' in data_dict:
        for obj in data_dict['objects']:
            # Handle objects with multiple labels and repeat bbox per label
            if multilabel_properties:
                for prop in multilabel_properties:

                    normed_coords = norm_bbox_coord(obj['coords'], width, height)
                    xmins.append(normed_coords[0])
                    ymins.append(normed_coords[1])
                    xmaxs.append(normed_coords[2])
                    ymaxs.append(normed_coords[3])

                    label_int_codes.append(label_map_dict[prop][obj[prop]])
                    label_text.append(obj[prop].encode('utf-8'))
                    difficult.append(obj['occluded'])

            # Handle objects with just 1 label (standard behavior)
            else:
                normed_coords = norm_bbox_coord(obj['coords'], width, height)
                xmins.append(normed_coords[0])
                ymins.append(normed_coords[1])
                xmaxs.append(normed_coords[2])
                ymaxs.append(normed_coords[3])

                label_int_codes.append(label_map_dict[obj['label']])
                label_text.append(obj['label'].encode('utf-8'))
                difficult.append(obj['occluded'])

    # Don't modify height/width until after normalized bboxes have been calculated
    if downsized:
        height = DOWNSAMP_IMG_SHP[0]
        width = DOWNSAMP_IMG_SHP[1]

    # Create tf.Example to store image, annotations, and metadata
    example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(
            data_dict['filename'].encode('utf8')),
        'image/img_id': dataset_util.int64_feature(img_id),
        'image/key/sha256': dataset_util.bytes_feature(key.encode('utf8')),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image.format.encode('utf8')),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),

        # Add object bounding boxes
        'image/object/class/label': dataset_util.int64_list_feature(label_int_codes),
        'image/object/class/text': dataset_util.bytes_list_feature(label_text),
        'image/object/difficult': dataset_util.int64_list_feature(difficult)
    }))

    return example


if __name__ == "__main__":
    bucket = s3_download_params['bucket']
    s3_profile = s3_download_params['s3_profile']
    s3_folder_prefix = s3_download_params['s3_folder_prefix']
    downsized = True
    if not op.isdir(LABEL_PARAMS['tf_output_dir']):
        os.mkdir(LABEL_PARAMS['tf_output_dir'])

    # for xml in LABEL_PARAMS['xml_left']:
    #     parsed_labels = parse_xml_examples(LABEL_PARAMS['xml_dir'], xml)

    for xml_fname in LABEL_PARAMS['xml_fnames']:
        #########################################################
        # Create dictionary of every data point from the CVAT XML
        #########################################################
        parsed_labels = parse_xml_examples(op.join(LABEL_PARAMS['xml_dir'], xml_fname))
        ############################################
        # Convert data samples to TF.Example objects
        ############################################
        examples = [dict_to_tf_example(bucket,
                                       s3_folder_prefix,
                                       s3_profile,
                                       parsed_label,
                                       LABEL_PARAMS['property_map_dict'],
                                       LABEL_PARAMS['multilabel_properties'])
                    for parsed_label in tqdm(parsed_labels, desc='Creating TF.Example objects.')]

        # Remove any empty examples (perhaps skipped because image didn't exist)
        filt_examples = [ex for ex in examples if ex is not None]

        #################################################################
        # Convert data samples to TF.Example objects and save as TFRecord
        #################################################################
        print(f'Filtered out {len(examples) - len(filt_examples)} examples '
              f'(total: {len(examples)}) that were `None`')

        # Package up into TF Record
        tf_output_fpath = op.join(LABEL_PARAMS['tf_output_dir'],
                                  Path(xml_fname).with_suffix('.tfrecord'))

        # TODO Consider sharding TFRecord files and making train/test/val split
        with tf.io.TFRecordWriter(str(tf_output_fpath)) as writer:
            for ex in filt_examples:
                writer.write(ex.SerializeToString())

        print(f'Finished writing to:\n{tf_output_fpath}\n')
