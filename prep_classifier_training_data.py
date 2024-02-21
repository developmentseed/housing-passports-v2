import os
import sys
import json
import cv2
import numpy as np
import pandas as pd

def clip_image_around_bbox_buffer(image, bbox, buffer=100):
    """
    Clips an image around a bounding box with a buffer.

    Args:
        image (ndarray): Input image.
        bbox (tuple): Bounding box coordinates (x1, y1, x2, y2).
        buffer (int): Buffer size.

    Returns:
        ndarray: Clipped image.
    """
    x1, y1, x2, y2 = bbox
    x1 -= buffer
    y1 -= buffer
    x2 += buffer
    y2 += buffer
    x1_ = max(0, int(x1))
    y1_ = max(0, int(y1))
    x2_ = min(int(x2), image.shape[1])
    y2_ = min(int(y2), image.shape[0])
    clipped_image = image[y1_:y2_, x1_:x2_]
    return clipped_image

def main(images_dir, annotation_json, side, out_dir):  

    annotation_json = open(annotation_json)
    annotation_json = json.load(annotation_json)  
    os.makedirs(out_dir, exist_ok=True)
    
    cntr = 0

    cumulative_annos = []
    
    for t in annotation_json['images']:
        tf = t['file_name']
        ti = t['id']
        im = cv2.imread(f"{images_dir}/{tf}")
        box_num = 0
        for gt in annotation_json['annotations']:
            if gt['image_id'] == ti:
                bb = gt['bbox']
                bbxyxy = (bb[0], bb[1], bb[0]+bb[2], bb[1]+bb[3])
                bbox_data = list(bbxyxy)
                try:
                    clipped_img = clip_image_around_bbox_buffer(im, bbox_data)
                    if len(clipped_img) > 0:

                        image_clipped_output_dirs = tf.split('/')
                        os.makedirs(os.path.join(out_dir, image_clipped_output_dirs[0]), exist_ok=True)
                        os.makedirs(os.path.join(out_dir, image_clipped_output_dirs[0], image_clipped_output_dirs[1]), exist_ok=True)
    
                        if os.path.exists(os.path.join(out_dir, tf)):
                            # Multiple boxes present in image
                            box_num=box_num+1
                            image_boxes_categories = {"img_id": gt['image_id'], "file_name": tf, "box": bbox_data, "image_name_clip": f"{tf[:-4]}_{box_num}.jpg", 
                                                      "ann_id": gt['id'], "complete": gt['attributes']['building_completeness'],
                                                      "condition": gt['attributes']['building_condition'],
                                                      "material": gt['attributes']['building_material'],
                                                      "security": gt['attributes']['building_security'],
                                                      "use": gt['attributes']['building_use']}
                            #print(image_boxes_categories)
                            cumulative_annos.append(image_boxes_categories)
                            cv2.imwrite(os.path.join(out_dir, f"{tf[:-4]}_{box_num}.jpg"), clipped_img)
                        else:
                            image_boxes_categories = {"img_id": gt['image_id'], "file_name": tf, "box": bbox_data, "image_name_clip": f"{tf}", 
                                                      "ann_id": gt['id'], "complete": gt['attributes']['building_completeness'],
                                                      "condition": gt['attributes']['building_condition'],
                                                      "material": gt['attributes']['building_material'],
                                                      "security": gt['attributes']['building_security'],
                                                      "use": gt['attributes']['building_use']}
                            #print(image_boxes_categories)
                            cumulative_annos.append(image_boxes_categories)
                            cv2.imwrite(os.path.join(out_dir, f"{tf}"), clipped_img)
                        cntr = cntr+1
                        print("Annotation count: ", cntr)
                except Exception as e:
                    # Print the error message if an exception occurs
                    print("An error occurred:", e, im, bbox_data)
    df_out = pd.DataFrame(cumulative_annos)
    df_out.to_csv(f"{out_dir}/cumulative_annos_{side}.csv")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prep_classifier_training_data.py <IMG_DIR> <ANN_JSON> <SIDE> <OUT_DIR>")
        sys.exit(1)
    IMG_DIR = sys.argv[1]
    ANN_JSON = sys.argv[2] # repeat for left and right side JSON annotations
    SIDE = sys.argv[3] # repeat for left and right side JSON annotations
    OUT_DIR =  sys.argv[4]
    main(IMG_DIR, ANN_JSON, SIDE, OUT_DIR)