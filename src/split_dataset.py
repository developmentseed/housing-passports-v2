import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

def split_dataset(data_path, focus_class, random_state=42):
    """Splits dataset into train, valid & test set based on approximate stratified sampling."""
    df = pd.read_csv(data_path)

    # List of possible strings
    augmented_strings = ['_0.jpg', '_1.jpg', '_2.jpg', '_3.jpg', '_4.jpg']
    
    # Create a new DataFrame where column values contain any string from the list
    augmented_df = df[df['file_name'].apply(lambda x: any(substring in x for substring in augmented_strings))]
    print(len(df), len(augmented_df))
    print(augmented_df.file_name.head(1))

    # Remove augmented samples from the original dataframe
    df = df[~df['file_name'].isin(augmented_df['file_name'])]

    # Create a combined feature column for stratified sampling
    df["feature"] = df[["complete", "condition", "security"]].apply(
        lambda x: "_".join(x.astype(str)), axis=1
    )

    augmented_df["feature"] = augmented_df[["complete", "condition", "security"]].apply(
        lambda x: "_".join(x.astype(str)), axis=1
    )
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
    if not os.path.exists("/home/ubuntu/model/housing-passports-v2/data/intermediate"):
        os.makedirs("/home/ubuntu/model/housing-passports-v2/data/intermediate")
    train_df.to_csv(f"/home/ubuntu/model/housing-passports-v2/data/intermediate/train_{focus_class}.csv", index=False)
    valid_df.to_csv(f"/home/ubuntu/model/housing-passports-v2/data/intermediate/valid_{focus_class}.csv", index=False)
    test_df.to_csv(f"/home/ubuntu/model/housing-passports-v2/data/intermediate/test_{focus_class}.csv", index=False)


if __name__ == "__main__":
    split_dataset(sys.argv[1], sys.argv[2])
