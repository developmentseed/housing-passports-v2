#!/usr/bin/env python
from setuptools import setup, find_packages
from imp import load_source
from os import path as op
import io

__version__ = load_source('housing_passports.version', 'housing_passports/version.py').__version__

here = op.abspath(op.dirname(__file__))

# get the dependencies and installs
with io.open(op.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if 'git+' not in x]

setup(
    name='housing-passports',
    author='Development Seed',
    author_email='wronk@developmentseed.org',
    version=__version__,
    description='Infrastructure resilience',
    url='https://github.com/housing-passports/',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='',
    entry_points={"console_scripts": [
        "passport_predict = housing_passports.local_inf_cli:local_inf",
        "passport_annot = housing_passports.local_inf_cli:save_annotated_image",
        "passport_db_export = housing_passports.db_package:export_to_db",
        "passport_link_db_detections = housing_passports.db_package:link_db_detections",
        "passport_distill_metadata = housing_passports.db_package:distill_building_metadata",
        "passport_detection_export = housing_passports.db_package:export_detection_geometry"]},
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=dependency_links,
)
