import lightning as L

from src.datamodule import HouseDataModule
from src.model import HPClassifier

L.seed_everything(42)


def main():
    # datamodule
    dm = HouseDataModule(
        img_dir="notebooks/output/images_clipped_buffered/",
        label_file="notebooks/data.csv",
        batch_size=128,
        num_workers=2,
    )
    dm.setup(stage="fit")

    # model
    model = HPClassifier()

    # trainer
    trainer = L.Trainer(
        devices="auto",
        accelerator="auto",
        max_epochs=10,
        precision="bf16-mixed",
    )
    trainer.fit(
        model,
        train_dataloaders=dm.train_dataloader(),
        val_dataloaders=dm.val_dataloader(),
    )


if __name__ == "__main__":
    main()
