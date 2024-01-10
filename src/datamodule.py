from pathlib import Path

from einops import rearrange
import pandas as pd
import matplotlib.pyplot as plt
import torch
import lightning as L
from sklearn.model_selection import train_test_split
from torchvision.io import read_image
from torchvision.transforms import v2
from torch.utils.data import Dataset, DataLoader


class HouseDataset(Dataset):
    def __init__(self, df, img_dir, transform=None):
        self.df = df
        self.img_dir = img_dir
        self.transform = transform

        self.complete = {"complete": 0, "incomplete": 1}
        self.condition = {"poor": 0, "fair": 1, "good": 2}
        self.material = {
            "mix-other-unclear": 0,
            "plaster": 1,
            "brick_or_cement-concrete_block": 2,
            "wood_polished": 3,
            "stone_with_mud-ashlar_with_lime_or_cement": 4,
            "corrugated_metal": 5,
            "wood_crude-plank": 6,
            "container-trailer": 7,
        }
        self.security = {"secured": 0, "unsecured": 1}
        self.use = {
            "residential": 0,
            "critical_infrastructure": 1,
            "mixed": 2,
            "commercial": 3,
        }

    def __getattr__(self, name):
        "Creates a reverse mapping for all the building properties"
        if name.startswith("r") and hasattr(self, name[1:]):
            _attr = getattr(self, name[1:])
            if isinstance(_attr, dict):
                return {v: k for k, v in _attr.items()}
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.img_dir / row.file_name
        img = read_image(str(img_path))

        # Convert string labels to integers using the mappings
        complete = self.complete[row.complete]
        condition = self.condition[row.condition]
        material = self.material[row.material]
        security = self.security[row.security]
        use = self.use[row.use]

        if self.transform:
            img = self.transform(img)

        return img, complete, condition, material, security, use

    def show(self, idx):
        img, complete, condition, material, security, use = self[idx]
        title = f"{self.rcomplete[complete]} | {self.rcondition[condition]} | {self.rmaterial[material]} | {self.rsecurity[security]} | {self.ruse[use]}"
        img = rearrange(img, "c h w -> h w c")
        plt.imshow(img)
        plt.axis("off")
        plt.title(title)


def resize_and_pad(target_width, target_height):
    def transform(image):
        # Original dimensions
        _, original_width, original_height = image.shape

        # Determine scaling factor and resize
        scaling_factor = min(
            target_width / original_width, target_height / original_height
        )
        new_width, new_height = int(original_width * scaling_factor), int(
            original_height * scaling_factor
        )
        resized_image = v2.Resize((new_height, new_width), antialias=True)(image)

        # Calculate padding
        padding_left = (target_width - new_width) // 2
        padding_top = (target_height - new_height) // 2
        padding_right = target_width - new_width - padding_left
        padding_bottom = target_height - new_height - padding_top

        # Pad the resized image
        padded_image = v2.Pad(
            (padding_left, padding_top, padding_right, padding_bottom),
            fill=0,
            padding_mode="constant",
        )(resized_image)

        return padded_image

    return transform


class HouseDataModule(L.LightningDataModule):
    def __init__(self, img_dir, label_file, batch_size, num_workers):
        self.img_dir = Path(img_dir)
        self.label_file = label_file
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.trn_tfm = v2.Compose(
            [
                resize_and_pad(224, 224),
                v2.RandomHorizontalFlip(p=0.5),
                v2.ToDtype(torch.float32, scale=True),
                v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        self.val_tfm = v2.Compose(
            [
                resize_and_pad(224, 224),
                v2.ToDtype(torch.float32, scale=True),
                v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def setup(self, stage=None):
        df = pd.read_csv(self.label_file)
        trn_df, val_df = train_test_split(df, test_size=0.2, shuffle=True)
        self.trn_ds = HouseDataset(trn_df, self.img_dir, self.trn_tfm)
        self.val_ds = HouseDataset(val_df, self.img_dir, self.val_tfm)

    def train_dataloader(self):
        return DataLoader(
            self.trn_ds,
            shuffle=True,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            pin_memory=True,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_ds,
            shuffle=True,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            pin_memory=True,
        )
