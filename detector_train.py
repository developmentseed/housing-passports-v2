import os
import sys
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultTrainer


def main(annotations_dir, images_dir):
    """
    Main function for training a Detectron2 model.

    Args:
        annotations_dir (str): Directory containing COCO annotations.
        images_dir (str): Directory containing images.

    Raises:
        ValueError: If the annotations directory or images directory is not provided.
    """
    # Check if annotations_dir and images_dir are provided
    if not annotations_dir or not images_dir:
        raise ValueError("Annotations directory and images directory must be provided.")

    # Register the partitioned COCO datasets for building detection
    register_coco_instances("hp_train", {}, os.path.join(annotations_dir, "instances_default_train.json"), images_dir)
    register_coco_instances("hp_val", {}, os.path.join(annotations_dir, "instances_default_val.json"), images_dir)
    register_coco_instances("hp_test", {}, os.path.join(annotations_dir, "instances_default_test.json"), images_dir)
    
    # Set up configuration details for the Detectron2 training experiment
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/retinanet_R_50_FPN_3x.yaml"))
    cfg.DATASETS.TRAIN = ("hp_train",)
    cfg.DATASETS.TEST = ("hp_val",)
    cfg.DATALOADER.NUM_WORKERS = 2
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/retinanet_R_50_FPN_3x.yaml")
    cfg.SOLVER.IMS_PER_BATCH = 2
    cfg.SOLVER.BASE_LR = 0.00025
    cfg.SOLVER.MAX_ITER = 10000 
    cfg.SOLVER.STEPS = []       
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 512
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1 

    # Create output directory if not exist
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # Initialize and train the model
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=True)
    trainer.train()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detector_train.py <IMG_DIR> <ANN_DIR>")
        sys.exit(1)
    IMG_DIR = sys.argv[1]
    ANN_DIR = sys.argv[2] # where the COCO json annotations are
    main(IMG_DIR, ANN_DIR)