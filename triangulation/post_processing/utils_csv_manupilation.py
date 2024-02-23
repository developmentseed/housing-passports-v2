"""
Utils to read in large csv for data manipulation

author: @developmentseed

utils_csv_manupilation.py

"""

import os
from os import makedirs, path as op
import json
import collections
import itertools 
import pandas as pd
import ast


def read_big_csv(csv, columns=None):
    """filter and rename tractory csv files

    Args:
        csv: csv file that contains gps coordination

    Returns:
        df: exported dataframe filtered columns and renamed
    """
    # csv is more than 500MB, so read data in chunks e.g. 5000 rows per chunk
    c_size = 5000
    if columns:
        select_cols = ['HEADING', 'IMAGE_ID', 'LAT', 'LONG']
        df_chunks_lst = [chuck_df for chuck_df in pd.read_csv(csv,
                                    chunksize=c_size, skipinitialspace=True, usecols=select_cols)]
    else:
        df_chunks_lst = [chuck_df for chuck_df in pd.read_csv(csv,
                                    chunksize=c_size, skipinitialspace=True)]

    df = pd.concat(df_chunks_lst)
    return df


def _filter_values(values, optimal_score):
    """filter detection by the optimal score

    Args:
        detection: the detection for each images
    Returns:
        new
    """
    values = ast.literal_eval(values)
    new_dict = dict(detection_scores=[],
       detection_classes =[],
       detection_boxes = [],
                   image_fname=None)
    for detection in values:
        if float(detection['detection_scores'])>= float(optimal_score[int(detection['detection_classes'])]):
            print(int(detection['detection_classes']), detection['detection_scores'], detection['detection_boxes'])
            new_dict['detection_scores'].append(detection['detection_scores'])
            new_dict['detection_classes'].append(int(detection['detection_classes']))
            new_dict['detection_boxes'].append(detection['detection_boxes'])
    return new_dict


def filter_detection_by_optimal_score(optimal_score, df, output_dir, col = ['tile', 'output']):
    """filter dataframe values by the given threshold

    Args:
        optimal_score: dictionary include the optimal key and value;
        df: the target dataframe

    Returns:
        (None): write each row into json file
    """
    df2dict = dict(zip(df[col[0]], df[col[1]]))
    for key, value in df2dict.items():
        new_dict = _filter_values(value, optimal_score)
        new_dict['image_fname']=key
        if not op.isdir(output_dir):
            makedirs(output_dir)
        nm = op.splitext(op.basename(key))[0]
        out_file = op.join(output_dir, f"{nm}.json")
        if op.isfile(out_file):
            continue
        else:
            with open(out_file, 'w') as f:
                json.dump(new_dict, f)

def aggregate_classes(optimal_score, df, col = ['tile', 'output']):
    """filter dataframe values by the given threshold

    Args:
        optimal_score: dictionary include the optimal key and value;
        df: the target dataframe

    Returns:
        (None): write each row into json file
    """
    all_cls = []
    df2dict = dict(zip(df[col[0]], df[col[1]]))
    for key, value in df2dict.items():
        new_dict = _filter_values(value, optimal_score)
        all_cls.append(new_dict['detection_classes'])

    # get all the detected classes and count the frequency
    freq = collections.defaultdict(int)
    for x in itertools.chain.from_iterable(all_cls):
        freq[x] +=1

    return dict(freq)
