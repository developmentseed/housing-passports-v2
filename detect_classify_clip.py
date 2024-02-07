import os
import sys
import glob
import cv2
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


def main(images_dir, detector_cpkt_path, classification_ckpt_path, output_dir, focus_class):
    """
    Main function for object detection and classification.

    Args:
        images_dir (str): Directory containing dataset images.
        detector_cpkt_path (str): Path to the detector checkpoint file.
        classification_ckpt_path (str): Path to the classification model checkpoint file.
        output_dir (str): Directory to save output files.
        focus_class (str): Class to focus on during classification.
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
    
    for t in glob.glob(f"{images_dir}/**/**/*.jpg"): #test_annotations['images']:
        tf = "/".join(t.split("/")[-3:]) #t['file_name']
        if os.path.exists(os.path.join(image_clipped_output, tf)):
            im = cv2.imread(os.path.join(image_clipped_output, tf)) 
            img = torch.tensor(im.transpose(2,0,1)).to(torch.float32)
            img = ToPILImage()(img)
            transform = Compose([
                Resize((512,512), antialias=True),
                ToTensor(),
                Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            img = transform(img)
            img = img.unsqueeze(0)
           
            categories = evaluate_classification_model(classification_model, img, classification_model.device)
            image_categories = {"image_name": tf, f"{focus_class}": categories[focus_class]}
            print(image_categories)
            cumulative_predictions.append(image_categories)
        else:
            im = cv2.imread(os.path.join(images_dir, tf))
            outputs = predictor(im)
            bb_preds = outputs["instances"].pred_boxes
            bb_scores = outputs["instances"].scores
            if bb_preds:
                for bb, sc in zip(bb_preds, bb_scores):
                    #bbxyxy = (bb[0], bb[1], bb[2], bb[3])
                    bbox_data = bb.tolist() #list(bbxyxy)
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
                           
                            categories = evaluate_classification_model(classification_model, img, classification_model.device)
                            image_boxes_categories = {"image_name": tf, "boxes": bbox_data, "box_scores": sc, f"{focus_class}": categories[focus_class]}
                            print(image_boxes_categories)
                            cumulative_predictions.append(image_boxes_categories)

                            image_clipped_output_dirs = tf.split('/')
                            os.makedirs(os.path.join(image_clipped_output, image_clipped_output_dirs[0]), exist_ok=True)
                            os.makedirs(os.path.join(image_clipped_output, image_clipped_output_dirs[0], image_clipped_output_dirs[1]), exist_ok=True)
                             
                            cv2.imwrite(os.path.join(image_clipped_output, tf), clipped_img)
                            cntr = cntr+1
                            print("Prediction count: ", cntr)
                    except Exception as e:
                        print(f"Exception: {e}")
                        pass
                
    df_out = pd.DataFrame(cumulative_predictions)
    df_out.to_csv(os.path.join(output_dir, f"{focus_class}_predictions.csv"))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])