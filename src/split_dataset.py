import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

def split_dataset(data_path, output_path, random_state=42):
    """Splits dataset into train, valid & test set based on approximate stratified sampling."""
    df = pd.read_csv(data_path)

    # Create a combined feature column for stratified sampling
    df["feature"] = df[["complete", "condition", "security"]].apply(
        lambda x: "_".join(x.astype(str)), axis=1
    )

    # Remove unnecessary column 
    df = df.drop(['Unnamed: 0'], axis=1)


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
    train_df.to_csv(f"{output_path}/train.csv", index=False)
    valid_df.to_csv(f"{output_path}/valid.csv", index=False)
    test_df.to_csv(f"{output_path}/test.csv", index=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_dataset.py <CSV_PATH> <OUTPUT_PATH>")
        sys.exit(1)
    CSV_PATH = sys.argv[1] # where the un-partitioned csv is
    OUTPUT_PATH = sys.argv[2]
    split_dataset(CSV_PATH, OUTPUT_PATH)

