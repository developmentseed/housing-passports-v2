"""
Utilities for converting CVAT XML to other formats.

@author: Development Seed
"""
import xml.etree.ElementTree as etree


def parse_image_filepath_v1(filepath):
    """Parse a partial filepath formatted as 'city/folder/camera_side/fname'."""
    city, folder, side, fname = filepath.split('/')

    # Return city to upper case to match folder naming on S3
    return city.upper(), folder, side, fname


def norm_bbox_coord(coord_tup, image_width, image_height):
    """Normalize CVAT bbox coordinates from pixel coord to image proportion [0, 1].

    Parameters
    ----------
    coord_tup: 4-iterable
        Pixel coords for x top left, y top left, x bottom right, y bottom right.
        Must maintain that order
    image_width: float
        In pixels
    image_eight: float
        In pixels

    Returns
    -------
    normed_coords: 4-iterable
        Normalized coords for x top left, y top left, x bottom right, y bottom right
        on interval [0, 1]
    """

    return (float(coord_tup[0]) / image_width,
            float(coord_tup[1]) / image_height,
            float(coord_tup[2]) / image_width,
            float(coord_tup[3]) / image_height)


def parse_xml_examples(xml_fpath):
    """Load and convert XML from CVAT into list of bounding boxes.

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

    print("Reading image annotations for task: '{}'".format(
        root.find('meta').find('task').find('name').text))
    image_entries = root.findall('image')
    all_image_annots = []

    for image in image_entries:
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
                                       occluded=int(bb.get('occluded', 0)),
                                       coords=coords)

            # Get all attribute labels for this bbox
            for attr in bb.findall('attribute'):
                bbox_attribute_dict[attr.get('name')] = attr.text

            img_dict['objects'].append(bbox_attribute_dict)

        all_image_annots.append(img_dict)

    return all_image_annots

def create_category_index_from_labelmap(labelmap_path, use_display_name=True):
    "Convert map files into index"
    category_index = {}
    with open(labelmap_path, 'r') as f:
        lines = f.readlines()

    current_class = None
    for line in lines:
        line = line.strip()
        if line.startswith('item {'):
            current_class = {}
        elif line.startswith('id:'):
            class_id = int(line.split(':')[-1].strip())
            current_class['id'] = class_id
        elif line.startswith('name:'):
            class_name = line.split(':')[-1].strip()[1:-1]
            current_class['name'] = class_name
        elif use_display_name and line.startswith('display_name:'):
            display_name = line.split(':')[-1].strip()[1:-1]
            current_class['display_name'] = display_name
        elif line.startswith('}'):
            if current_class:
                category_index[class_id] = current_class
                current_class = None

    return category_index
