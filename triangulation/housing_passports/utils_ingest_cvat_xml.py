"""
Constuct TF Records file from CVAT xml

"""
import io
import os
import os.path as op
import xml.etree.ElementTree as etree
import hashlib

from tqdm import tqdm
import tensorflow as tf
import PIL
from object_detection.utils import  dataset_util


def parse_xml_examples(xml_fpath):
    """Load and convert XML from CVAT into list of bounding boxes

    OpenCV's Computer Vision Annotation Tool is here:
    https://github.com/opencv/cvat

    Parameters
    ----------
    filepath: str
        Path to XML file on disk.

    Returns
    -------
    all_image_annots: list
        List of bounding box tuples (X-TL, Y-TL, X-BR, Y-BR) for all images in
        the XML file. This format is reversed from numpy coordinate ordering.
    """

    # Error checking
    root = etree.parse(xml_fpath).getroot()
    children = [child.tag for child in root]
    if 'meta' not in children or 'image' not in children:
        raise ValueError('Problem reading XML, missing features')

    print("Reading image annotations for task: {}\n".format(
        root.find('meta').find('task').find('name').text))
    image_entries = root.findall('image')
    all_image_annots = []

    for image in tqdm(image_entries):

        # Loop through all bboxes in image and save them as list of tuples
        img_dict = dict(height=image.get('height'),
                        width=image.get('width'),
                        filename=image.get('name'),
                        id=image.get('id'),
                        objects=[])

        for bb in image.findall('box'):
            coords = [round(float(bb.get(coord_key))) for coord_key in
                      ['xtl', 'ytl', 'xbr', 'ybr']]

            bbox_attribute_dict = dict(label=bb.get('label'),
                                       occluded=image.get('occluded'),
                                       coords=coords)

            # Get all attribute labels for this bbox
            for attr in bb.findall('attribute'):
                bbox_attribute_dict[attr.get('name')] = attr.text

            img_dict['objects'].append(bbox_attribute_dict)

        all_image_annots.append(img_dict)

    return all_image_annots


def dict_to_tf_example(data_dict, dataset_directory, label_map_dict,
                       downsampled=True):
    """Convert XML derived dict to tf.Example proto.

    Note: this function normalizes the bounding box coordinates provided by the
    raw data.

    Parameters:
    -----------
    data_dict: dict
        PASCAL XML fields for a single image
    dataset_directory: str
        Path to root directory holding VOC-formatted dataset
    label_map_dict: dict
        A map from string label names to integers ids.
    downsampled: bool
        Whether to use 512x512 downsampled images.

    Returns:
    --------
    example: The converted tf.Example.

    Raises:
    -------
    ValueError: if the image pointed to by data['path'] is not a valid JPEG
    """

    # Get filepath to image
    if downsampled:
        full_path = op.join(dataset_directory, 'DownSampledImages',
                            '{}-512{}'.format(*op.splitext(data_dict['filename'])))
    else:
        full_path = op.join(dataset_directory, data_dict['filename'])

    # Load image and get bytestring
    with tf.gfile.GFile(full_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format != 'JPEG':
        raise ValueError('Image format not JPEG')

    # Set some image level properties
    key = hashlib.sha256(encoded_jpg).hexdigest()
    width = int(data_dict['width'])
    height = int(data_dict['height'])
    img_id = int(data_dict['id'])

    # Initialize lists to hold each object annotation in the image
    xmin = []
    ymin = []
    xmax = []
    ymax = []

    label_building = []
    label_building_text = []
    label_designed = []
    label_designed_text = []
    label_material = []
    label_material_text = []
    label_construction = []
    label_construction_text = []

    if 'objects' in data_dict:
        for obj in data_dict['objects']:
            xmin.append(float(obj['coords'][0]) / width)
            ymin.append(float(obj['coords'][1]) / height)
            xmax.append(float(obj['coords'][2]) / width)
            ymax.append(float(obj['coords'][3]) / height)

            label_building.append(label_map_dict[obj['label']])
            label_building_text.append(obj['label'].encode('utf8'))

            label_material.append(label_map_dict[obj['material']])
            label_material_text.append(obj['material'].encode('utf8'))

            label_designed.append(label_map_dict[obj['design']])
            label_designed_text.append(obj['design'].encode('utf8'))

            label_construction.append(label_map_dict[obj['construction']])
            label_construction_text.append(obj['construction'].encode('utf8'))

    # Don't modify height/width until after normalized bboxes have been calculated
    if downsampled:
        width = int(512)
        height = int(512)

    # Create tf.Example to store image, annotations, and metadata
    example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(
            data_dict['filename'].encode('utf8')),
        'image/camera_id': dataset_util.int64_feature(img_id),
        'image/key/sha256': dataset_util.bytes_feature(key.encode('utf8')),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature('jpeg'.encode('utf8')),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),

        #XXX Set the class to the desired attribute
        'image/object/class/label': dataset_util.int64_list_feature(label_construction),
        'image/object/class/text': dataset_util.bytes_list_feature(label_construction_text),

        'image/object/building/label': dataset_util.int64_list_feature(label_building),
        'image/object/building/text': dataset_util.bytes_list_feature(label_building_text),
        'image/object/material/label': dataset_util.int64_list_feature(label_material),
        'image/object/material/text': dataset_util.bytes_list_feature(label_material_text),
        'image/object/designed/label': dataset_util.int64_list_feature(label_designed),
        'image/object/designed/text': dataset_util.bytes_list_feature(label_designed_text),
        'image/object/construction/label': dataset_util.int64_list_feature(label_construction),
        'image/object/construction/text': dataset_util.bytes_list_feature(label_construction_text),
    }))

    return example


if __name__ == "__main__":

    ### Test that utils work correctly

    # Get list of images from parsed xmls
    img_dir = '/Volumes/ext3/Data/housing_passports/68/Borde_Rural/Images'
    xml_fpath = '/Volumes/ext3/Data/housing_passports/cvat/building_classification_right_images.xml'
    tf_output_dir = '/Volumes/ext3/Data/housing_passports/tf_records'
    tf_output_fpath = op.join(tf_output_dir,
                              op.splitext(op.basename(xml_fpath))[0] +
                              '.tfrecord')

    if not op.isdir(tf_output_dir):
        os.mkdir(tf_output_dir)

    # Set label dict to assign into to each object class
    label_map_dict = {'building':1,
                      'brick':1, 'concrete':2, 'tin':3, 'wood':4, 'painted':5,
                      'other/unclear':6,
                      'incomplete':1, 'complete':2,
                      'undesigned':1, 'designed':2}

    parsed_labels = parse_xml_examples(xml_fpath)

    # Load pairs, create TF.Example objects
    examples = [dict_to_tf_example(parsed_label, img_dir, label_map_dict)
                for parsed_label in tqdm(parsed_labels, desc='Creating TF.Example objects.')]

    # Package up into TF Record
    with tf.python_io.TFRecordWriter(tf_output_fpath) as writer:
        for example in tqdm(examples, desc='Writing TF.Example objects'):
            writer.write(example.SerializeToString())
