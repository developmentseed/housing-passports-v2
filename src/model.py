import torch
import torch.nn as nn
import torch.nn.functional as F
import lightning as L
from torchvision import models


class HPClassifier(L.LightningModule):
    def __init__(
        self,
        num_completeness=2,
        num_conditions=3,
        num_materials=8,
        num_securities=2,
        num_uses=4,
    ):
        super().__init__()
        self.save_hyperparameters()

        backbone = models.resnet18(pretrained=True)
        in_features = backbone.fc.in_features

        self.backbone = nn.Sequential(*list(backbone.children())[:-1])
        # Freeze the backbone
        for param in self.backbone.parameters():
            param.requires_grad = False

        # Head for each of the building properties
        # complete
        self.complete_head = nn.Linear(in_features, num_completeness)

        # condition
        self.condition_head = nn.Linear(in_features, num_conditions)

        # material
        self.material_head = nn.Linear(in_features, num_materials)

        # security
        self.security_head = nn.Linear(in_features, num_securities)

        # use
        self.use_head = nn.Linear(in_features, num_uses)

    def forward(self, xb):
        features = self.backbone(xb)
        features = torch.flatten(features, 1)

        complete_logits = self.complete_head(features)
        condition_logits = self.condition_head(features)
        material_logits = self.material_head(features)
        security_logits = self.security_head(features)
        use_logits = self.use_head(features)

        return (
            complete_logits,
            condition_logits,
            material_logits,
            security_logits,
            use_logits,
        )

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=1e-3)

    def shared_step(self, batch, phase):
        img, complete_idx, condition_idx, material_idx, security_idx, use_idx = batch
        (
            complete_logits,
            condition_logits,
            material_logits,
            security_logits,
            use_logits,
        ) = self(img)

        complete_loss = F.cross_entropy(complete_logits, complete_idx)
        condition_loss = F.cross_entropy(condition_logits, condition_idx)
        material_loss = F.cross_entropy(material_logits, material_idx)
        security_loss = F.cross_entropy(security_logits, security_idx)
        use_loss = F.cross_entropy(use_logits, use_idx)

        loss = complete_loss + condition_loss + material_loss + security_loss + use_loss
        self.log(
            f"{phase}_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            logger=True,
        )

        return loss

    def training_step(self, batch, batch_idx):
        return self.shared_step(batch, "train")

    def validation_step(self, batch, batch_idx):
        return self.shared_step(batch, "val")
