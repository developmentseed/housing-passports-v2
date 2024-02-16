"""
Example showing how to send a data example to a TF Serving image

@author:Development Seed

Sidenote, check out the command:
    `saved_model_cli show --dir ./ --all`
    to see what types of inputs the model expects/returns. Run from the version
    folder of the exported model (e.g., .../001)

Once a server is running, you can get a detailed list of metadata from something like:
http://localhost:8501/v1/models/od_building_mat/metadata
"""

import os
import os.path as op
import json
import pprint
import time
import base64
import requests

import numpy as np
import skimage.io as sio
#import matplotlib as mpl
from skimage import img_as_ubyte
from skimage.transform import rescale
from PIL import ImageFont

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
#mpl.use('Agg')
#from matplotlib import pyplot as plt


def url_image_to_b64_string(url):
    """Convert a url to a UTF-8 coded string of base64 bytes.

    Notes
    -----
    Use this if you need to download tiles from a tile server and send them to
    a prediction server. This will convert them into a string representing
    base64 format which is more efficient than many other options.

    """
    # GET data from url
    response = requests.get(url)
    if not response.ok:
        print('Error getting image from {}'.format(url))

    # Convert to base64 and then encode in UTF-8 for future transmission
    b64 = base64.b64encode(response.content)
    b64_string = b64.decode("utf-8")

    return b64_string


################################
# Build local prediction request
################################
print('\nBuilding request from local images')
ml_mode = 'design'
server_endpoint = f'http://localhost:8501/v1/models/od_building_{ml_mode}:predict'

hp_dir = '/Volumes/ext3/Data/housing_passports'
preds_save_dir = op.join(hp_dir, 'obj_detection', f'preds_{ml_mode}_sample')
cat_index = label_map_util.create_category_index_from_labelmap(
    op.join(hp_dir, f'tf_records/{ml_mode}_190220/{ml_mode}_od.pbtxt'),
    use_display_name=True)

data_dir = op.join(hp_dir, '68/Borde_Rural/Images/DownSampledImages')
img_fnames = [img_fname for img_fname in os.listdir(data_dir)
              if '1-512' in img_fname or '3-512' in img_fname]

img_fnames = img_fnames[274:279:2]
img_fpaths = [op.join(data_dir, img_fname) for img_fname in img_fnames]

instances = []
images = []
for img_fpath in img_fpaths:

    img = sio.imread(img_fpath)
    images.append(img.tolist())

    with open(img_fpath, 'rb') as imageFile:
        b64_image = base64.b64encode(imageFile.read())
        instances.append({'inputs': {'b64': b64_image.decode('utf-8')}})

payload = json.dumps({"instances": instances})

#########################
# Send prediction request
#########################
print('Num of images in payload: {}'.format(len(instances)))

start = time.time()
r = requests.post(server_endpoint, data=payload)

elapsed = time.time() - start

#########################
# Print results
#########################
pp = pprint.PrettyPrinter()
preds = json.loads(r.content)['predictions']
print('\nPredictions from local images:')
for pi, pred in enumerate(preds):
    print(f'\nPrediction number {pi}')
    n_ods = int(pred['num_detections'])
    for prop in ['detection_classes', 'detection_scores', 'detection_boxes']:
        pp.pprint(pred[prop][:n_ods])

print(f'\nElapsed time: {elapsed} sec')


#########################
# Visualize results
#########################

full_scale_img_dir = op.join(hp_dir, '68/Borde_Rural/Images')


for img_fpath, pred in zip(img_fpaths, preds):
    base_name, ext = op.splitext(op.basename(img_fpath))

    new_img_fpath = op.join(full_scale_img_dir, base_name[:-4] + ext)
    image_np_pre = sio.imread(new_img_fpath)
    image_np = rescale(image_np_pre,
                       anti_aliasing=True, multichannel=True, scale=0.5,
                       clip=False)
    image_np = img_as_ubyte(image_np)

    # Increase font size
    #font = ImageFont.truetype('./AmericanTypewriter.ttc', 120)

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

    sio.imsave(op.join(preds_save_dir, base_name + ext), image_np)
