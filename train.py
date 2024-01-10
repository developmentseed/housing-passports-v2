from aim.pytorch_lightning import AimLogger
import lightning as L
from lightning.pytorch.callbacks import LearningRateMonitor, ModelCheckpoint

from src.datamodule import HouseDataModule
from src.model import HPClassifier
from src.callbacks import BackboneFreezeUnfreeze

L.seed_everything(42)


def main():
    logger = AimLogger(
        experiment="test-aim-1",
        train_metric_prefix="train_",
        val_metric_prefix="val_",
    )
    # datamodule
    dm = HouseDataModule(
        img_dir="notebooks/output/images_clipped_buffered/",
        label_file="notebooks/data.csv",
        batch_size=256,
        num_workers=8,
    )
    dm.setup(stage="fit")

    # model
    model = HPClassifier(lr=1e-3)

    # Callbacks
    lr_cb = LearningRateMonitor(
        logging_interval="step",
        log_momentum=True,
    )
    ckpt_cb = ModelCheckpoint(
        monitor="val_loss",
        mode="min",
        save_top_k=2,
        save_last=True,
        verbose=True,
        filename="epoch:{epoch}-step:{step}-loss:{val_loss:.3f}",
        auto_insert_metric_name=False,
    )
    backbone_freeze_unfreeze_cb = BackboneFreezeUnfreeze(unfreeze_at_epoch=10)

    # trainer
    trainer = L.Trainer(
        devices="auto",
        accelerator="auto",
        max_epochs=20,
        precision="bf16-mixed",
        logger=logger,
        callbacks=[lr_cb, ckpt_cb, backbone_freeze_unfreeze_cb],
    )
    trainer.fit(
        model,
        train_dataloaders=dm.train_dataloader(),
        val_dataloaders=dm.val_dataloader(),
    )


if __name__ == "__main__":
    main()
