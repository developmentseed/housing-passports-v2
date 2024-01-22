import torch
import torch.nn as nn
import torch.nn.functional as F
import torchmetrics
import lightning as L
from torchvision import models

from src.loss import FocalLoss


class HPClassifier(L.LightningModule):
    def __init__(
        self,
        lr=1e-3,
        num_completeness=2,
        num_conditions=3,
        num_materials=8,
        num_securities=2,
        num_uses=4,
    ):
        super().__init__()
        self.save_hyperparameters()

        backbone = models.resnet34(pretrained=True)
        in_features = backbone.fc.in_features

        self.backbone = nn.Sequential(*list(backbone.children())[:-1])

        # Head for each of the building properties
        # complete
        # self.complete_head = nn.Sequential(
        #     nn.Linear(in_features, 256),
        #     nn.ReLU(),
        #     nn.Dropout(0.5),
        #     nn.Linear(256, num_completeness),
        # )

        # # condition
        # self.condition_head = nn.Sequential(
        #     nn.Linear(in_features, 256),
        #     nn.ReLU(),
        #     nn.Dropout(0.5),
        #     nn.Linear(256, num_conditions),
        # )

        # # material
        # self.material_head = nn.Sequential(
        #     nn.Linear(in_features, 256),
        #     nn.ReLU(),
        #     nn.Dropout(0.5),
        #     nn.Linear(256, num_materials),
        # )

        # # security
        # self.security_head = nn.Sequential(
        #     nn.Linear(in_features, 256),
        #     nn.ReLU(),
        #     nn.Dropout(0.5),
        #     nn.Linear(256, num_securities),
        # )

        # # use
        # self.use_head = nn.Sequential(
        #     nn.Linear(in_features, 256),
        #     nn.ReLU(),
        #     nn.Dropout(0.5),
        #     nn.Linear(256, num_uses),
        # )
        self.complete_head = nn.Linear(in_features, num_completeness)
        # self.condition_head = nn.Linear(in_features, num_conditions)
        # self.material_head = nn.Linear(in_features, num_materials)
        # self.security_head = nn.Linear(in_features, num_securities)
        # self.use_head = nn.Linear(in_features, num_uses)

        self.complete_f1 = torchmetrics.F1Score(
            task="multiclass", num_classes=num_completeness
        )
        # self.condition_f1 = torchmetrics.F1Score(
        #     task="multiclass", num_classes=num_conditions
        # )
        # self.material_f1 = torchmetrics.F1Score(
        #     task="multiclass", num_classes=num_materials
        # )
        # self.security_f1 = torchmetrics.F1Score(
        #     task="multiclass", num_classes=num_securities
        # )
        # self.use_f1 = torchmetrics.F1Score(task="multiclass", num_classes=num_uses)

    def forward(self, xb):
        features = self.backbone(xb)
        features = torch.flatten(features, 1)

        complete_logits = self.complete_head(features)
        # condition_logits = self.condition_head(features)
        # material_logits = self.material_head(features)
        # security_logits = self.security_head(features)
        # use_logits = self.use_head(features)

        return (
            complete_logits,
            # condition_logits,
            # material_logits,
            # security_logits,
            # use_logits,
        )

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.parameters(), lr=self.hparams.lr)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer, T_0=10, T_mult=2, eta_min=self.hparams.lr * 100, last_epoch=-1
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
            },
        }

    def shared_step(self, batch, phase):
        img, complete_idx, condition_idx, material_idx, security_idx, use_idx = batch
        (
            complete_logits,
            # condition_logits,
            # material_logits,
            # security_logits,
            # use_logits,
        ) = self(img)

        complete_preds = torch.argmax(complete_logits, dim=1)
        # condition_preds = torch.argmax(condition_logits, dim=1)
        # material_preds = torch.argmax(material_logits, dim=1)
        # security_preds = torch.argmax(security_logits, dim=1)
        # use_preds = torch.argmax(use_logits, dim=1)

        complete_f1 = self.complete_f1(complete_preds, complete_idx)
        # condition_f1 = self.condition_f1(condition_preds, condition_idx)
        # material_f1 = self.material_f1(material_preds, material_idx)
        # security_f1 = self.security_f1(security_preds, security_idx)
        # use_f1 = self.use_f1(use_preds, use_idx)

        # complete_loss_focal = FocalLoss(
        #     gamma=2.0, weight=torch.as_tensor([0.16, 0.84], device=self.device)
        # )
        # complete_loss = complete_loss_focal(complete_logits, complete_idx)

        # condition_loss_focal = FocalLoss(
        #     weight=torch.as_tensor([0.19, 0.09, 0.72], device=self.device)
        # )
        # condition_loss = condition_loss_focal(condition_logits, condition_idx)

        # material_loss_focal = FocalLoss(
        #     weight=torch.as_tensor(
        #         [0.0046, 0.0017, 0.018, 0.026, 0.196, 0.099, 0.25, 0.39],
        #         device=self.device,
        #     )
        # )
        # material_loss = material_loss_focal(material_logits, material_idx)

        # security_loss_focal = FocalLoss(
        #     weight=torch.as_tensor([0.75, 0.25], device=self.device)
        # )
        # security_loss = security_loss_focal(security_logits, security_idx)

        # use_loss_focal = FocalLoss(
        #     weight=torch.as_tensor([0.009, 0.759, 0.115, 0.115], device=self.device)
        # )
        # use_loss = use_loss_focal(use_logits, use_idx)

        complete_loss = F.cross_entropy(
            complete_logits,
            complete_idx,
            weight=torch.as_tensor([0.16, 0.84], device=self.device),
        )
        # complete_loss = F.cross_entropy(
        #     complete_logits,
        #     complete_idx,
        # )

        # condition_loss = F.cross_entropy(
        #     condition_logits,
        #     condition_idx,
        #     weight=torch.as_tensor([0.19, 0.09, 0.72], device=self.device),
        # )
        # material_loss = F.cross_entropy(
        #     material_logits,
        #     material_idx,
        #     weight=torch.as_tensor(
        #         [0.0046, 0.0017, 0.018, 0.026, 0.196, 0.099, 0.25, 0.39],
        #         device=self.device,
        #     ),
        # )
        # security_loss = F.cross_entropy(
        #     security_logits,
        #     security_idx,
        #     weight=torch.as_tensor([0.75, 0.25], device=self.device),
        # )
        # use_loss = F.cross_entropy(
        #     use_logits,
        #     use_idx,
        #     weight=torch.as_tensor([0.009, 0.759, 0.115, 0.115], device=self.device),
        # )

        loss = (
            complete_loss
            # + condition_loss
            # + (material_loss / 4)
            # + security_loss
            # + use_loss
        )
        self.log(
            f"{phase}_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            logger=True,
        )

        # for properties in ("complete", "condition", "material", "security", "use"):
        for properties in ("complete",):
            self.log(
                f"{phase}_{properties}_f1",
                locals()[f"{properties}_f1"],
                prog_bar=True,
                logger=True,
            )

        return loss

    def training_step(self, batch, batch_idx):
        return self.shared_step(batch, "train")

    def validation_step(self, batch, batch_idx):
        return self.shared_step(batch, "val")

    def test_step(self, batch, batch_idx):
        return self.shared_step(batch, "test")
