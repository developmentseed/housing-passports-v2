"""
Construct label txt files from CVAT XML labels

@author: Development Seed
"""

import os.path as op
from pathlib import Path

from tqdm import tqdm

from utils_convert import (parse_xml_examples, parse_image_filepath_v1,
                           norm_bbox_coord)
from config_data import (label_params as LABEL_PARAMS,
                         label_map_dict_whole_building,
                         label_map_dict_whole_building_bogota,
                         label_map_dict_building_parts,
                         whole_building_properties,
                         whole_building_properties_bogota)


def dict_to_text(data_dict, label_map_dict,
                 multilabel_properties=None):
    """Convert one image label to text for saving.

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

    Returns
    -------
    label_str: str
        One or more objects with each as one line of text. Format is
        <class_id> <xtl> <ytl> <xbr> <ybr> <occluded>
        The coordinate values are normalized to interval [0, 1]
    """

    xmins, ymins, xmaxs, ymaxs = [], [], [], []
    label_int_codes = []
    difficults = []

    text_bbox_labels = []

    if 'objects' in data_dict:
        for obj in data_dict['objects']:
            # Handle objects with multiple labels and repeat bbox per label
            if multilabel_properties:
                for prop in multilabel_properties:
                    normed_coords = norm_bbox_coord(obj['coords'],
                                                    int(data_dict['width']),
                                                    int(data_dict['height']))
                    xmins.append(normed_coords[0])
                    ymins.append(normed_coords[1])
                    xmaxs.append(normed_coords[2])
                    ymaxs.append(normed_coords[3])

                    label_int_codes.append(label_map_dict[prop][obj[prop]])
                    difficults.append(obj['occluded'])

            # Handle objects with just 1 label (standard behavior)
            else:
                normed_coords = norm_bbox_coord(obj['coords'],
                                                int(data_dict['width']),
                                                int(data_dict['height']))
                xmins.append(normed_coords[0])
                ymins.append(normed_coords[1])
                xmaxs.append(normed_coords[2])
                ymaxs.append(normed_coords[3])

                label_int_codes.append(label_map_dict[obj['label']])
                difficults.append(int(obj['occluded']))

        # Create text for each label
        for xmin, ymin, xmax, ymax, label_int_code, difficult in zip(
                xmins, ymins, xmaxs, ymaxs, label_int_codes, difficults):

            text_bbox_labels.append(f'{label_int_code} {xmin:0.5f} {ymin:0.5f} {xmax:0.5f} {ymax:0.5f} {difficult}\n')

    return text_bbox_labels


if __name__ == "__main__":
    for xml_fname in LABEL_PARAMS['xml_fnames']:

        # Create dictionary of every data point from the CVAT XML
        parsed_labels = parse_xml_examples(op.join(LABEL_PARAMS['xml_dir'], xml_fname))

        # Convert data samples to text and save
        for parsed_label in tqdm(parsed_labels, 'Creating text files with labels'):

            # Get save directory and generate text filename
            city, folder, _, fname = parse_image_filepath_v1(parsed_label['filename'])
            fpath_txt = op.join(LABEL_PARAMS['img_head_dir'], city, folder,
                                LABEL_PARAMS['text_label_dirname'],
                                Path(fname).with_suffix('.txt'))

            # Check that directory exists
            Path(fpath_txt).parent.mkdir(parents=True, exist_ok=True)

            # Generate labels as text strings
            labels = dict_to_text(parsed_label,
                                  LABEL_PARAMS['property_map_dict'],
                                  LABEL_PARAMS['multilabel_properties'])

            # Write contents to simple text file. One line per bbox
            with open(fpath_txt, 'w') as f:
                f.writelines(labels)

        print(f'Finished writing labels from:\n{xml_fname}\n')
