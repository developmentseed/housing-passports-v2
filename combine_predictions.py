import sys
import ast
import re
import pandas as pd

def extract_float(tensor_string):
    # Convert tensors to float
    float_value = re.findall(r'-?\d+\.\d+', tensor_string)
    return float(float_value[0])

def main(output_dir):
    """
    Merge individual prediction DataFrames into one DataFrame and save it.

    This function reads prediction DataFrames for different categories from CSV files,
    merges them horizontally based on the 'image_name' column, 
    and saves the resulting DataFrame as a CSV file.

    Parameters:
    output_dir (str): The directory where prediction CSV files are located and where
                      the merged CSV file will be saved.

    Returns:
    None
    """
    # Read prediction DataFrames from CSV files
    df_complete_predictions = pd.read_csv(f"{output_dir}/complete_predictions.csv")
    df_condition_predictions = pd.read_csv(f"{output_dir}/condition_predictions.csv")
    df_security_predictions = pd.read_csv(f"{output_dir}/security_predictions.csv")
    df_material_predictions = pd.read_csv(f"{output_dir}/material_predictions.csv")
    df_use_predictions = pd.read_csv(f"{output_dir}/use_predictions.csv")

    # Drop the 'Unnamed: 0' column from each DataFrame
    df_complete_predictions.drop(columns=['Unnamed: 0'], inplace=True)
    df_condition_predictions.drop(columns=['Unnamed: 0'], inplace=True)
    df_security_predictions.drop(columns=['Unnamed: 0'], inplace=True)
    df_material_predictions.drop(columns=['Unnamed: 0'], inplace=True)
    df_use_predictions.drop(columns=['Unnamed: 0'], inplace=True)

    # Merge DataFrames horizontally based on the 'image_name' column
    all_predictions = pd.merge(df_use_predictions, df_material_predictions, on='image_name')
    all_predictions = pd.merge(all_predictions, df_security_predictions, on='image_name')
    all_predictions = pd.merge(all_predictions, df_condition_predictions, on='image_name')
    all_predictions = pd.merge(all_predictions, df_complete_predictions, on='image_name')

    # Convert tensor scores to float
    all_predictions['box_scores'] = all_predictions['box_scores'].apply(extract_float)

    # Convert tensor boxes to float
    all_predictions['boxes_float'] = all_predictions['boxes'].apply(ast.literal_eval)

    # Convert float boxes to int
    all_predictions['boxes_int'] = all_predictions['boxes_float'].apply(lambda x: [int(elem) for elem in x])

    # Save the merged DataFrame as a CSV file
    all_predictions.to_csv(f"{output_dir}/all_predictions.csv")

if __name__ == "__main__":
    main(sys.argv[1])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python combine_predictions.py <OUTPUT_DIR> <ANN_DIR>")
        sys.exit(1)
    OUTPUT_DIR = sys.argv[1] # where the class-wise csv predictions are
    main(OUTPUT_DIR)
