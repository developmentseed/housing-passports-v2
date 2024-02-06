import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

def split_dataset(data_path, focus_class, output_path, random_state=42):
    """Splits dataset into train, valid & test set based on approximate stratified sampling."""
    df = pd.read_csv(data_path)

    # Augmented image string identifiers
    augmented_strings = ['_0.jpg', '_1.jpg', '_2.jpg', '_3.jpg', '_4.jpg']
    
    # Separate the augmented images from the dataframe
    augmented_df = df[df['file_name'].apply(lambda x: any(substring in x for substring in augmented_strings))]

    # Remove augmented samples from the original dataframe
    df = df[~df['file_name'].isin(augmented_df['file_name'])]

    # Create a combined feature column for stratified sampling
    df["feature"] = df[["complete", "condition", "security"]].apply(
        lambda x: "_".join(x.astype(str)), axis=1
    )

    augmented_df["feature"] = augmented_df[["complete", "condition", "security"]].apply(
        lambda x: "_".join(x.astype(str)), axis=1
    )

    # Remove unnecessary column 
    df = df.drop(['Unnamed: 0'], axis=1)
    augmented_df = augmented_df.drop(['Unnamed: 0'], axis=1)


    train_df, temp_df = train_test_split(
        df,
        test_size=0.3,
        random_state=random_state,
        stratify=df["feature"],
        shuffle=True,
    )
    valid_df, test_df = train_test_split(
        temp_df,
        test_size=0.4,
        random_state=random_state,
        stratify=temp_df["feature"],
        shuffle=True,
    )

    # Stratify and split the augmented samples just for training and validation
    train_df_augmented, valid_df_augmented = train_test_split(
        augmented_df,
        test_size=0.3,
        random_state=random_state,
        stratify=augmented_df["feature"],
        shuffle=True,
    )

    # Combine the augmented dataframes with the original train and validation dataframes
    train_df = pd.concat([train_df, train_df_augmented], axis=0, ignore_index=True)
    valid_df = pd.concat([valid_df, valid_df_augmented], axis=0, ignore_index=True)

    # Shufle dataframes with augmented samples added
    train_df = train_df.sample(frac=1).reset_index(drop=True)
    valid_df = valid_df.sample(frac=1).reset_index(drop=True)

    # Print stats
    for dataset in ("train", "valid", "test"):
        print("-" * 50)
        print(f"{dataset.capitalize()} dataset stats: ")
        for property in ("complete", "condition", "material", "security", "use"):
            print(
                locals()[f"{dataset}_df"][property].value_counts(normalize=True) * 100
            )
        print("-" * 50)

    # Drop feature column
    for dataset in (train_df, valid_df, test_df):
        dataset.drop("feature", axis=1, inplace=True)

    # Save datasets
    if not os.path.exists(f"{output_path}"):
        os.makedirs(f"{output_path}")
    train_df.to_csv(f"{output_path}/train_{focus_class}.csv", index=False)
    valid_df.to_csv(f"{output_path}/valid_{focus_class}.csv", index=False)
    test_df.to_csv(f"{output_path}/test_{focus_class}.csv", index=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_dataset.py <CSV_PATH> <FOCUS_CLASS> <OUTPUT_PATH>")
        sys.exit(1)
    CSV_PATH = sys.argv[1] # where the un-partitioned csv is
    FOCUS_CLASS = sys.argv[2]
    OUTPUT_PATH = sys.argv[3]
    split_dataset(CSV_PATH, FOCUS_CLASS, OUTPUT_PATH)

