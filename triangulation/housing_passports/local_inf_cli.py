"""
Run inference locally using running TF Serving image

@author Development Seed
"""

import os
import os.path as op
from itertools import zip_longest
import json
import base64
import requests

import numpy as np
from skimage import img_as_ubyte
import skimage.io as sio
from skimage.transform import rescale
import click
from tqdm import tqdm

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


def _grouper(iterable, n, fillvalue=None):
    "Itertool recipe to collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def _filter_pred_keys(pred_dict, keep_keys=('detection_scores',
                                            'detection_classes',
                                            'detection_boxes')):
    """Apply filter to keep a limited number of dict keys"""
    new_pred_dict = {}
    for key in keep_keys:
        new_pred_dict[key] = pred_dict[key]

    return new_pred_dict


def _apply_score_thresh(pred_dict, score_thresh):
    """Remove predictions below some score threshold"""

    new_pred_dict = {}
    good_inds = np.asarray(pred_dict['detection_scores']) >= score_thresh

    for key in pred_dict.keys():
        new_pred_dict[key] = np.asarray(pred_dict[key])[good_inds].tolist()

    return new_pred_dict


def _stringify_preds(pred_dict):
    """Create an iterable of string objects ready for text file write."""

    obj_classes = pred_dict['detection_classes']
    obj_scores = pred_dict['detection_scores']
    obj_boxes = pred_dict['detection_boxes']

    lines = []
    for obj_class, obj_score, obj_box in zip(obj_classes, obj_scores,
                                             obj_boxes):
        lines.append(f'{int(obj_class)} {obj_box} {obj_score}')

    return lines


@click.command(short_help="Generate images with annotations overlayed.")
@click.argument('json-fpath', type=click.Path(exists=True))
@click.argument("cat-pbtxt-fpath", type=click.Path(exists=True))
#                help="pbtxt file with mapping from category float to string name")
@click.argument("source-directory", type=str)
#                help=("Directory with streetview images (potentially higher "
#                      "resolution than used in prediction"))
@click.option("--save-directory", type=str, default='.',
              help="Directory to save annotated images")
@click.option("--rescale-factor", type=float, default=1.,
              help="Rescale source image by some factor")
def save_annotated_image(json_fpath, cat_pbtxt_fpath, source_directory,
                         save_directory='.', rescale_factor=1.):
    """Save bounding box predictions as annotations on an image"""

    # Load JSON of image predictions and class indicies
    with open(json_fpath, 'r') as json_file:
        pred = json.load(json_file)

    cat_index = label_map_util.create_category_index_from_labelmap(
        cat_pbtxt_fpath, use_display_name=True)

    # Generate file paths to save/load image
    img_fname = op.splitext(op.basename(json_fpath))[0] + '.jpg'
    img_load_fpath = op.join(source_directory, img_fname)
    img_save_fpath = op.join(save_directory, img_fname)

    # Load image and rescale if necessary
    image_np = sio.imread(img_load_fpath)
    if rescale_factor != 1.:
        image_np = rescale(image_np, anti_aliasing=True, multichannel=True,
                           scale=rescale_factor, clip=False)
        image_np = img_as_ubyte(image_np)

    # Increase font size
    # Move arial.ttf to /models/research/object_detection/utils
    #font = ImageFont.truetype('./arial.ttc', 36)

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.asarray(pred['detection_boxes']),
        np.asarray(pred['detection_classes'], dtype=np.uint8),
        np.asarray(pred['detection_scores']),
        cat_index,
        instance_masks=pred.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=10)

    # Save output; time-consuming for large images
    sio.imsave(img_save_fpath, image_np)


@click.command(short_help="Run ML inference on local directory of images")
@click.argument("image-directory", type=str, nargs=1)
@click.argument("url-endpoint", type=str, nargs=1)
@click.option("--save-directory", type=str, default=None,
              help="Directory to save images. Defaults to `image-directory`")
@click.option("--score-thresh", type=float, default=0.5,
              help="Minimum model score to keep a detection. Valid interval: (0, 1]")
@click.option("--batch-size", type=int, default=1,
              help="Size of each image batch")
@click.option("--img-ext", type=str, default=['jpg'], multiple=True,
              help="Image file extension")
def local_inf(image_directory, url_endpoint, save_directory, score_thresh,
              batch_size, img_ext):
    """Run inference on local directory using TF Serving image.

    Parameters
    ----------
    image_directory: str
        String specifiying the directory path where all images will be inferred
    url_endpoint: str
        URL of running server (e.g., TF Serving container) where images will
        be sent for inference.
    save_directory: str
        Directory to save predictions. Defaults to same directory as images.
    score_thresh: float
        Minimum score to include a model detection in the final results.
    batch_size: int
        Number of images per inference batch. Defaults to 1.
    img_ext: list of str
        Extensions of files to run prediction on. Defaults to `jpg`.
    """

    if not isinstance(img_ext, list):
        img_ext = list(img_ext)
    if save_directory is None:
        save_directory = image_directory
    if not 0. < score_thresh <= 1.:
        raise ValueError('`score_thresh` must fall on interval (0, 1]')

    img_fnames = [img_fname for img_fname in os.listdir(image_directory)
                  if op.splitext(img_fname)[1][1:] in img_ext]

    # Iterate through groups of images
    for img_group in tqdm(_grouper(img_fnames, batch_size)):

        ###################################
        # Create a batch of data to predict

        instances = []
        for batch_img_fname in img_group:
            if batch_img_fname is not None:
                with open(op.join(image_directory, batch_img_fname), 'rb') as image_file:
                    b64_image = base64.b64encode(image_file.read())
                    #instances.append({'inputs': {'b64': b64_image.decode('utf-8')}})
                    instances.append({'b64': b64_image.decode('utf-8')})

        ################
        # Run prediction

        payload = json.dumps({"instances": instances})
        resp = requests.post(url_endpoint, data=payload)
        preds = json.loads(resp.content)['predictions']

        ##########################################
        # Save results to text file for each image

        for batch_img_fname, pred_dict in zip(img_group, preds):
            save_fname = op.splitext(batch_img_fname)[0] + '.json'

            # Remove some keys, and then apply score threshold
            pred_dict = _filter_pred_keys(pred_dict)
            pred_dict = _apply_score_thresh(pred_dict, score_thresh)
            pred_dict['image_fname'] = batch_img_fname  # Add filename

            # Save to disk
            with open(op.join(save_directory, save_fname), 'w') as json_file:
                json.dump(pred_dict, json_file)
