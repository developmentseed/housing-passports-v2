import ast
import os
import sys
import glob
import cv2
import re
import numpy as np
import pandas as pd
import torch
from torchvision.transforms import Compose, Resize, ToTensor, Normalize, ToPILImage
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.engine.defaults import DefaultPredictor
from src.datamodule import HouseDataModule
from src.model import HPClassifier


def load_configuration(config_file):
    """
    Load configuration from a YAML file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        CfgNode: Configuration options.
    """
    cfg = get_cfg()
    cfg.merge_from_file(config_file)
    return cfg



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

def extract_float(tensor_string):
    # Convert tensors to float
    float_value = re.findall(r'-?\d+\.\d+', tensor_string)
    return float(float_value[0])

def load_classification_model(checkpoint_path):
    """
    Loads a classification model from a checkpoint.

    Args:
        checkpoint_path (str): Path to the checkpoint file.

    Returns:
        HPClassifier: Loaded classification model.
    """
    try:
        model = HPClassifier.load_from_checkpoint(checkpoint_path)
        return model
    except Exception as e:
        print(f"Failed to load model from {checkpoint_path}: {e}")
        sys.exit(1)

def evaluate_classification_model(model, img, device):
    """
    Evaluates a classification model on an image.

    Args:
        model (HPClassifier): Classification model.
        img (Tensor): Input image tensor.
        device (str): Device for model evaluation.

    Returns:
        dict: Predicted classes for different categories.
    """
    categories = {
        "complete": {"preds": [], "labels": [], "names": ["complete", "incomplete"]},
        "condition": {"preds": [], "labels": [], "names": ["poor", "fair", "good"]},
        "material": {
            "preds": [],
            "labels": [],
            "names": [
                "mix-other-unclear", "plaster", "brick_or_cement-concrete_block",
                "wood_polished", "stone_with_mud-ashlar_with_lime_or_cement",
                "corrugated_metal", "wood_crude-plank", "container-trailer",
            ],
        },
        "security": {"preds": [], "labels": [], "names": ["secured", "unsecured"]},
        "use": {
            "preds": [],
            "labels": [],
            "names": ["residential", "critical_infrastructure", "mixed", "commercial"],
        },
    }

    with torch.no_grad():
        logits = model(img.to(device))
        preds = [torch.argmax(logit, dim=1).cpu().numpy() for logit in logits]
        for key, pred in zip(categories.keys(), preds):
            categories[key]["preds"].extend(pred)

    predicted_classes = {}
    for category, data in categories.items():
        predicted_index = data['preds'][0]
        predicted_class = data['names'][predicted_index]
        predicted_classes[category] = predicted_class
    return predicted_classes


def main(images_dir, detector_cpkt_path, classification_ckpt_path, output_dir):
    """
    Main function for object detection and classification.

    Args:
        images_dir (str): Directory containing dataset images.
        detector_cpkt_path (str): Path to the detector checkpoint file.
        classification_ckpt_path (str): Path to the classification model checkpoint file.
        output_dir (str): Directory to save output files.
    """

    # Load configuration from file
    cfg = load_configuration(model_zoo.get_config_file("COCO-Detection/retinanet_R_50_FPN_3x.yaml"))

    # Set up Detectron2 model for inference
    cfg.MODEL.WEIGHTS = os.path.join(detector_cpkt_path)
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    predictor = DefaultPredictor(cfg)


    classification_model = load_classification_model(classification_ckpt_path)
    classification_model.to(classification_model.device)  

    image_clipped_output = os.path.join(output_dir, "inference_images_clipped_buffered/")
    os.makedirs(image_clipped_output, exist_ok=True)

    cumulative_predictions = []
    
    cntr = 0
    
    for t in glob.glob(f"{images_dir}/**/**/*.jpg"): 
        tf = "/".join(t.split("/")[-3:])
        
        im = cv2.imread(os.path.join(images_dir, tf))
        outputs = predictor(im)
        bb_preds = outputs["instances"].pred_boxes
        bb_scores = outputs["instances"].scores
        box_num = 0
        if bb_preds:
            for bb, sc in zip(bb_preds, bb_scores):
                bbox_data = bb.tolist() 
                try:
                    clipped_img = clip_image_around_bbox_buffer(im, bbox_data)
                    if len(clipped_img) > 0:
                        img = torch.tensor(clipped_img.transpose(2,0,1)).to(torch.float32)
                        img = ToPILImage()(img)
                        transform = Compose([
                            Resize((512,512), antialias=True),
                            ToTensor(),
                            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                        ])
                        img = transform(img)
                        img = img.unsqueeze(0)

                        image_clipped_output_dirs = tf.split('/')
                        os.makedirs(os.path.join(image_clipped_output, image_clipped_output_dirs[0]), exist_ok=True)
                        os.makedirs(os.path.join(image_clipped_output, image_clipped_output_dirs[0], image_clipped_output_dirs[1]), exist_ok=True)
                        
                        if os.path.exists(os.path.join(image_clipped_output, tf)):
                            box_num=box_num+1
                            categories = evaluate_classification_model(classification_model, img, classification_model.device)
                            image_boxes_categories = {"image_name": tf, "boxes": bbox_data, "box_scores": sc, "complete": categories["complete"], "condition": categories["condition"], "material": categories["material"], "security": categories["security"], "use": categories["use"], "image_name_clip": f"{tf[:-4]}_{box_num}.jpg"}
                            print(image_boxes_categories)
                            cumulative_predictions.append(image_boxes_categories)
                            cv2.imwrite(os.path.join(image_clipped_output, f"{tf[:-4]}_{box_num}.jpg"), clipped_img)
                        else:
                            categories = evaluate_classification_model(classification_model, img, classification_model.device)
                            image_boxes_categories = {"image_name": tf, "boxes": bbox_data, "box_scores": sc, "complete": categories["complete"], "condition": categories["condition"], "material": categories["material"], "security": categories["security"], "use": categories["use"], "image_name_clip": f"{tf}"}
                            print(image_boxes_categories)
                            cumulative_predictions.append(image_boxes_categories)
                            cv2.imwrite(os.path.join(image_clipped_output, f"{tf}"), clipped_img)
                        cntr = cntr+1
                        print("Prediction count: ", cntr)
                except Exception as e:
                    print(f"Exception: {e}")
                    pass
                
    df_out = pd.DataFrame(cumulative_predictions)
    # Convert tensor scores to float
    #df_out['box_scores'] = df_out['box_scores'].apply(extract_float)

    # Convert tensor boxes to float
    #df_out['boxes_float'] = df_out['boxes'].apply(ast.literal_eval)

    # Convert float boxes to int
    #df_out['boxes_int'] = df_out['boxes_float'].apply(lambda x: [int(elem) for elem in x])

    df_out.to_csv(os.path.join(output_dir, f"detection_classification_predictions.csv"))

    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_classify_clip.py <IMG_DIR> <DET_CPKT_PATH> <CLASS_CPKT_PATH> <OUTPUT_DIR>")
        sys.exit(1)
    IMG_DIR = sys.argv[1]
    DET_CPKT_PATH = sys.argv[2]
    CLASS_CPKT_PATH =  sys.argv[3]
    OUTPUT_DIR = sys.argv[4]
    main(IMG_DIR, DET_CPKT_PATH, CLASS_CPKT_PATH, OUTPUT_DIR)