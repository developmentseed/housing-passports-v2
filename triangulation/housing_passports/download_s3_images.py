"""
Download multiple folders/neighborhoods of images from S3

@author: Development Seed
"""

import os
import os.path as op
import boto3
from tqdm import tqdm

from housing_passports.config_data import s3_download_params as DL_PARAMS


def s3_download_dir(client, bucket, s3_dir_prefix, s3_dir_suffix, local_dir,
                    skip_existing=True):
    """Download an S3 directory

    Parameters
    ----------
    client
        boto client
    bucket: str
        S3 bucket name
    s3_dir_prefix: str
        Portion of filepath to directory on S3. Will *not* be included in local
        filepath when writing to local disk.
    s3_dir_suffix: str
        Portion of filepath to directory on S3. *Will* be included in local
        filepath when writing to local disk.
    local_dir: str
        Head of local directory for writing to local disk. Will be combined
        with the s3_dir_suffix.
    skip_existing: bool
        Whether or not to skip files if they already exist on disk.
    """

    paginator = client.get_paginator('list_objects')
    print(f'\nDownloading for {s3_dir_suffix}')

    for result in paginator.paginate(Bucket=bucket, Delimiter='/',
                                     Prefix=op.join(s3_dir_prefix,
                                                    s3_dir_suffix)):

        for s3_file in tqdm(result.get('Contents', []), total=-1):
            dest_pathname = op.join(local_dir, s3_dir_suffix,
                                    op.basename(s3_file.get('Key')))
            if not op.exists(op.dirname(dest_pathname)):
                os.makedirs(op.dirname(dest_pathname))
            if skip_existing and op.exists(dest_pathname):
                continue
            client.download_file(bucket, s3_file.get('Key'), dest_pathname)


if __name__ == '__main__':

    session = boto3.Session(profile_name=DL_PARAMS['s3_profile_name'])
    client = session.client('s3')

    for suffix in DL_PARAMS['folders']:
        s3_download_dir(client,
                        DL_PARAMS['bucket'],
                        DL_PARAMS['s3_folder_prefix'],
                        suffix,
                        DL_PARAMS['local_dir'])
