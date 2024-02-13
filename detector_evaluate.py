import os
import sys
import json
import cv2
import torch
from torchmetrics import detection
from torchmetrics.functional.detection import intersection_over_union
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultPredictor
from pprint import pprint

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

def load_test_annotations(annotations_dir):
    """
    Load test dataset annotations from a JSON file.

    Args:
        annotations_dir (str): Path to the directory containing annotations.

    Returns:
        dict: Test dataset annotations.
    """
    with open(os.path.join(annotations_dir, "instances_default_test.json")) as file:
        return json.load(file)

def get_image_path(image_id, images_data):
    """
    Get the file path of an image given its ID.

    Args:
        image_id (int): Image ID.
        images_data (list): List of image data dictionaries.

    Returns:
        str: File path of the image.
    """
    return next((image["file_name"] for image in images_data if image["id"] == image_id), None)

def convert_xywh_to_xyxy(bbox_list):
    """
    Convert bounding box coordinates from xywh to xyxy format.

    Args:
        bbox_list (list): List of bounding boxes in xywh format.

    Returns:
        list: List of bounding boxes in xyxy format.
    """
    return [[bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]] for bbox in bbox_list]

def get_ground_truth_annotations(image_id, dataset_dicts):
    """
    Get ground truth annotations for an image.

    Args:
        image_id (int): Image ID.
        dataset_dicts (dict): Dataset dictionary containing image annotations.

    Returns:
        list: Ground truth annotations for the image.
    """
    return dataset_dicts[image_id]["annotations"]

def main(annotations_dir, images_dir, cpkt_path):
    """
    Main function for evaluating object detection performance.

    Args:
        annotations_dir (str): Path to the directory containing dataset annotations.
        images_dir (str): Path to the directory containing dataset images.
        cpkt_path (str): Path to the trained model checkpoint.
    """
    # Register the partitioned COCO datasets for building detection
    register_coco_instances("hp_train", {}, os.path.join(annotations_dir, "instances_default_train.json"), images_dir)
    register_coco_instances("hp_val", {}, os.path.join(annotations_dir, "instances_default_val.json"), images_dir)
    register_coco_instances("hp_test", {}, os.path.join(annotations_dir, "instances_default_test.json"), images_dir)

    # Load test dataset annotations
    test_annotations = load_test_annotations(annotations_dir)

    # Load configuration from file
    cfg = load_configuration(model_zoo.get_config_file("COCO-Detection/retinanet_R_50_FPN_3x.yaml"))

    # Set up Detectron2 model for inference
    cfg.MODEL.WEIGHTS = cpkt_path
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    predictor = DefaultPredictor(cfg)

    # Use the test dataset
    dataset_name = "hp_test"

    # Load metadata and dataset
    metadata = MetadataCatalog.get(dataset_name)
    dataset_dicts = DatasetCatalog.get(dataset_name)

    # Lists to store predicted and ground truth bounding boxes
    outputs_test_preds = []
    outputs_test_gt = []

    # Iterate over annotations in the test dataset
    for annotation in test_annotations["annotations"]:
        # Get the image path from the test dataset
        image_path = get_image_path(annotation["image_id"], test_annotations["images"])

        # Read the image using OpenCV
        im = cv2.imread(os.path.join(images_dir, image_path))

        # Make predictions using the trained model
        outputs = predictor(im)

        try:
            # Get ground truth annotations for the current image
            gt_boxes = get_ground_truth_annotations(annotation["image_id"], dataset_dicts)

            # Check if there are both predicted and ground truth bounding boxes
            if gt_boxes and outputs["instances"].pred_boxes:
                # Convert ground truth bounding boxes to the required format (xywh -> xyxy)
                gt_boxes = convert_xywh_to_xyxy([ann["bbox"] for ann in gt_boxes])

                # Convert predicted bounding boxes and labels to tensors
                pred_boxes = torch.stack([torch.tensor(bbox) for bbox in outputs["instances"].pred_boxes])
                gt_boxes = torch.stack([torch.tensor(bbox) for bbox in gt_boxes])
                labels_preds = torch.ones(len(outputs["instances"].pred_boxes), dtype=torch.int32)
                labels_gts = torch.ones(len(gt_boxes), dtype=torch.int32)

                # Create dictionaries for ground truth and predicted bounding boxes
                gt = {'image_id': annotation['image_id'], 'labels': labels_gts, 'boxes': gt_boxes}
                prd = {'image_id': annotation['image_id'], 'labels': labels_preds, 'boxes': pred_boxes,
                       'scores': outputs["instances"].scores}

                # Append the dictionaries to the respective lists
                outputs_test_preds.append(prd)
                outputs_test_gt.append(gt)

        except Exception as e:
            # Handle exceptions, e.g., when ground truth annotations are not available
            print(f"Exception: {e}")
            pass

    # Calculate mAP
    m = detection.mean_ap.MeanAveragePrecision(box_format='xyxy', iou_type='bbox', iou_thresholds=[0.0], rec_thresholds=None, max_detection_thresholds=None, class_metrics=False)
    m.update(preds=outputs_test_preds, target=outputs_test_gt)
    print("mAP: ")
    pprint(m.compute()['map'])

    # Calculate IoU
    device = 'cuda:0'
    outputs_test_preds_tensor = [{key: torch.tensor(value, device=device) for key, value in item.items()} for item in outputs_test_preds]
    outputs_test_gt_tensor = [{key: torch.tensor(value, device=device) for key, value in item.items()} for item in outputs_test_gt]
    
    ious = []
    for p, g in zip(outputs_test_preds_tensor, outputs_test_gt_tensor):
        iou = intersection_over_union(p['boxes'], g['boxes'])
        ious.append(iou)
    
    # Stack the tensors along a new dimension (dimension 0)
    stacked_ious = torch.stack(ious, dim=0)
    
    # Calculate the mean along the stacked dimension
    average_iou = torch.mean(stacked_ious, dim=0)
    
    print("mIoU: ", average_iou)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detector_evaluate.py <ANN_DIR> <IMG_DIR> <CPKT_PATH>")
        sys.exit(1)
    ANN_DIR = sys.argv[1] # where the COCO json annotations are
    IMG_DIR = sys.argv[2]
    CPKT_PATH =  sys.argv[3]
    main(ANN_DIR, IMG_DIR, CPKT_PATH)
