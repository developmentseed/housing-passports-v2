import sys
import torch
import numpy as np
from src.datamodule import HouseDataModule
from src.model import HPClassifier
from sklearn.metrics import classification_report
import seaborn as sns
import matplotlib.pyplot as plt


def load_model(checkpoint_path):
    try:
        model = HPClassifier.load_from_checkpoint(checkpoint_path)
        return model
    except Exception as e:
        print(f"Failed to load model from {checkpoint_path}: {e}")
        sys.exit(1)


def evaluate_model(model, dataloader, device):
    categories = {
        "complete": {"preds": [], "labels": [], "names": ["complete", "incomplete"]},
        "condition": {"preds": [], "labels": [], "names": ["poor", "fair", "good"]},
        "material": {
            "preds": [],
            "labels": [],
            "names": [
                "mix-other-unclear",
                "plaster",
                "brick_or_cement-concrete_block",
                "wood_polished",
                "stone_with_mud-ashlar_with_lime_or_cement",
                "corrugated_metal",
                "wood_crude-plank",
                "container-trailer",
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
        for batch in dataloader():
            img, *labels = batch
            logits = model(img.to(device))
            preds = [torch.argmax(logit, dim=1).cpu().numpy() for logit in logits]

            for key, (pred, label) in zip(categories.keys(), zip(preds, labels)):
                categories[key]["preds"].extend(pred)
                categories[key]["labels"].extend(label.cpu().numpy())

    return categories


def print_classification_reports(categories):
    for category, data in categories.items():
        print(f"\nCategory: {category}")
        print(
            classification_report(
                data["labels"], data["preds"], target_names=data["names"]
            )
        )


def main(ckpt_path, img_dir, data_dir):
    dm = HouseDataModule(
        img_dir=img_dir,
        data_dir=data_dir,
        batch_size=16,
        num_workers=1,
    )
    dm.setup(stage="fit")

    model = load_model(ckpt_path)
    model.to(model.device)  # Ensure model is on the correct device

    categories = evaluate_model(model, dm.val_dataloader, model.device)
    print_classification_reports(categories)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python classifier_evaluate.py <CHECKPOINT_PATH> <IMG_DIR> <DATA_DIR>")
        sys.exit(1)
    CKPT_PATH = sys.argv[1]
    IMG_DIR = sys.argv[2]
    DATA_DIR = sys.argv[3] # where the partitioned csvs are
    main(CKPT_PATH, IMG_DIR, DATA_DIR)
