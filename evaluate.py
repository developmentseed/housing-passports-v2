import torch
import numpy as np
from src.datamodule import HouseDataModule
from src.model import HPClassifier
import matplotlib.pyplot as plt
import torch.nn.functional as F
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

CKPT_PATH = ".aim/complete-ce-weighted-full2/b585539aa6864aa9be8e27fa/checkpoints/epoch:15-step:528-loss:0.669.ckpt"

dm = HouseDataModule(
    img_dir="notebooks/output/images_clipped_buffered/",
    data_dir="data/intermediate",
    batch_size=16,
    num_workers=1,
)
dm.setup(stage="fit")

model = HPClassifier.load_from_checkpoint(CKPT_PATH)

complete = {"preds": [], "labels": []}

with torch.no_grad():
    for batch in dm.val_dataloader():
        img, complete_idx, condition_idx, material_idx, security_idx, use_idx = batch
        (
            complete_logits,
            # condition_logits,
            # material_logits,
            # security_logits,
            # use_logits,
        ) = model(img.to(model.device))
        # complete_preds, condition_preds, material_preds, security_preds, use_preds = (
        #     torch.argmax(complete_logits, dim=1),
        #     torch.argmax(condition_logits, dim=1),
        #     torch.argmax(material_logits, dim=1),
        #     torch.argmax(security_logits, dim=1),
        #     torch.argmax(use_logits, dim=1),
        # )
        complete_preds = torch.argmax(complete_logits, dim=1)
        complete["preds"].extend(complete_preds.cpu().numpy())
        complete["labels"].extend(complete_idx.cpu().numpy())
        # condition["preds"].extend(condition_preds.cpu().numpy())
        # condition["labels"].extend(condition_idx.cpu().numpy())
        # material["preds"].extend(material_preds.cpu().numpy())
        # material["labels"].extend(material_idx.cpu().numpy())
        # security["preds"].extend(security_preds.cpu().numpy())
        # security["labels"].extend(security_idx.cpu().numpy())
        # use["preds"].extend(use_preds.cpu().numpy())
        # use["labels"].extend(use_idx.cpu().numpy())

print(
    classification_report(
        complete["labels"],
        complete["preds"],
        labels=[0, 1],
        target_names=["complete", "incomplete"],
    )
)
