import sys
from aim.pytorch_lightning import AimLogger
import lightning as L
from lightning.pytorch.callbacks import LearningRateMonitor, ModelCheckpoint

from src.datamodule import HouseDataModule
from src.model import HPClassifier
from src.callbacks import BackboneFreezeUnfreeze

L.seed_everything(42, workers=True)


def main(name):
    logger = AimLogger(
        experiment=name,
        train_metric_prefix="train_",
        val_metric_prefix="val_",
    )
    # datamodule
    dm = HouseDataModule(
        img_dir="notebooks/output/images_clipped_buffered/",
        data_dir="data/intermediate/",
        batch_size=128,
        num_workers=8,
    )
    dm.setup()

    # model
    model = HPClassifier(lr=1e-3)

    # Callbacks
    lr_cb = LearningRateMonitor(
        logging_interval="step",
        log_momentum=True,
    )
    ckpt_cb = ModelCheckpoint(
        monitor="val_totalf1",
        mode="max",
        save_top_k=2,
        save_last=True,
        verbose=True,
        filename="epoch:{epoch}-step:{step}-loss:{val_loss:.3f}-f1:{val_totalf1:.3f}",
        auto_insert_metric_name=False,
    )
    backbone_freeze_unfreeze_cb = BackboneFreezeUnfreeze(unfreeze_at_epoch=10)

    # trainer
    trainer = L.Trainer(
        devices="auto",
        accelerator="auto",
        max_epochs=50,
        precision="bf16-mixed",
        logger=logger,
        callbacks=[lr_cb, ckpt_cb, backbone_freeze_unfreeze_cb],
    )

    # fit
    trainer.fit(
        model,
        train_dataloaders=dm.train_dataloader(),
        val_dataloaders=dm.val_dataloader(),
    )

    # test
    trainer.test(
        ckpt_path="best",
        dataloaders=dm.test_dataloader(),
    )


if __name__ == "__main__":
    main(sys.argv[1])
