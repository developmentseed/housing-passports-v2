"""
Configuration parameters for creating training data

@author: Development Seed
"""

import os
import os.path as op

DOWNSAMP_IMG_SHP = (512, 512, 3)  # Height, Width, Channels

whole_building_properties = ['material', 'completeness', 'use', 'security', 'condition']#, 'vintage']
whole_building_properties_bogota = ['material', 'design', 'construction']
building_parts = ['window', 'door', 'garage', 'disaster_mitigation']

# Set label dict to assign into to each object class
label_map_dict_building_parts = {'window': 1, 'door': 2, 'garage': 3, 'disaster_mitigation': 4}
label_map_dict_whole_building = {'material':{'brick_or_cement-concrete_block':1, 'plaster':2, 'wood_polished':3, 'wood_crude-plank':4,
                                             'adobe':5, 'corrugated_metal':6, 'stone_with_mud-ashlar_with_lime_or_cement':7, 'container-trailer':8,
                                             'plant_material':9, 'mix-other-unclear':10},
                                 'completeness':{'complete':11, 'incomplete': 12},
                                 'use':{'residential':13, 'mixed':14, 'non_residential':15},
                                 'security':{'unsecured':16, 'secured':17},
                                 'condition':{'average':18, 'poor':19, 'good':20}}
                                 #'vintage':{'not_defined':21, 'pre_1940': 22, '1941_1974':23, '1975_1999':24, '2000_now':25}}

label_map_dict_whole_building_bogota = {'brick':1, 'concrete':2, 'tin':3, 'wood':4, 'painted':5, 'other/unclear':6,
                                        'incomplete':7, 'complete':8,
                                        'undesigned':9, 'designed':10}

# Parameters for downloading images from S3
s3_download_params = dict(bucket='wbg-geography01',
                          s3_folder_prefix='GEP/DRONE/',
                          local_dir=op.join(os.environ['EXT_DATA_DIR'],
                                            'housing_passports/data/streetview/'),
                          s3_profile_name='housing_passports',
                          folders=['LIMA/119_CubeImage/downsized/',
                                   'LIMA/120a_CubeImage/downsized/',
                                   'LIMA/120b_CubeImage/downsized/',
                                   'LIMA/120c_CubeImage/downsized/',
                                   'LIMA/120d_CubeImage/downsized/',
                                   'LIMA/122_CubeImage/downsized/',
                                   'LIMA/123_CubeImage/downsized/',
                                   'LIMA/124a_CubeImage/downsized/',
                                   'LIMA/124b_CubeImage/downsized/',
                                   'LIMA/131a_CubeImage/downsized/',
                                   'LIMA/131b_CubeImage/downsized/',
                                   'LIMA/131c_CubeImage/downsized/',
                                   'LIMA/132_CubeImage/downsized/',
                                   'LIMA/133_CubeImage/downsized/',

                                   'CARTAGENA/134_CubeImage/downsized/',
                                   'CARTAGENA/135_CubeImage/downsized/',
                                   'CARTAGENA/136_CubeImage/downsized/',
                                   'CARTAGENA/137_CubeImage/downsized/',
                                   'CARTAGENA/138_CubeImage/downsized/',
                                   'CARTAGENA/139_CubeImage/downsized/',
                                   'CARTAGENA/140_CubeImage/downsized/',
                                   'CARTAGENA/141_CubeImage/downsized/',

                                   'NEIVA/142a_CubeImage/downsized/',
                                   'NEIVA/142b_CubeImage/downsized/',
                                   'NEIVA/143_CubeImage/downsized/',
                                   'NEIVA/144_CubeImage/downsized/',
                                   'NEIVA/145_CubeImage/downsized/',
                                   'NEIVA/146_CubeImage/downsized/',
                                   'NEIVA/147_CubeImage/downsized/',
                                   'NEIVA/148_CubeImage/downsized/',
                                   'NEIVA/149_CubeImage/downsized/',
                                   'NEIVA/150a_CubeImage/downsized/',
                                   'NEIVA/150b_CubeImage/downsized/',
                                   'NEIVA/151a_CubeImage/downsized/',
                                   'NEIVA/151b_CubeImage/downsized/',
                                   'NEIVA/153_CubeImage/downsized/',

                                   'STMAARTEN/155_CubeImage/downsized/',
                                   'STMAARTEN/156_CubeImage/downsized/',
                                   'STMAARTEN/157_CubeImage/downsized/',
                                   'STMAARTEN/159a_CubeImage/downsized/',
                                   'STMAARTEN/159b_CubeImage/downsized/',
                                   'STMAARTEN/160_CubeImage/downsized/',
                                   'STMAARTEN/164_CubeImage/downsized/',
                                   'STMAARTEN/166a_CubeImage/downsized/',
                                   'STMAARTEN/166b_CubeImage/downsized/',
                                   'STMAARTEN/167_CubeImage/downsized/',
                                   'STMAARTEN/168a_CubeImage/downsized/',
                                   'STMAARTEN/168b_CubeImage/downsized/',
                                   'STMAARTEN/169_CubeImage/downsized/',
                                   'STMAARTEN/170a_CubeImage/downsized/',
                                   'STMAARTEN/170b_CubeImage/downsized/',
                                   'STMAARTEN/171_CubeImage/downsized/',
                                   'STMAARTEN/172_Cubeimage/downsized/',
                                   'STMAARTEN/173_CubeImage/downsized/',
                                   'STMAARTEN/175_CubeImage/downsized/',
                                   'STMAARTEN/175b_CubeImage/downsized/',
                                   'STMAARTEN/176_CubeImage/downsized/',
                                   'STMAARTEN/177_CubeImage/downsized/',
                                   'STMAARTEN/178a_CubeImage/downsized/',
                                   'STMAARTEN/178b_CubeImage/downsized/',
                                   'STMAARTEN/178c_CubeImage/downsized/',
                                   'STMAARTEN/178d_CubeImage/downsized/',
                                   'STMAARTEN/178e_CubeImage/downsized/',
                                   'STMAARTEN/178f_CubeImage/downsized/',
                                   'STMAARTEN/178g_CubeImage/downsized/',
                                   'STMAARTEN/180_CubeImage/downsized/',
                                   'STMAARTEN/182a_CubeImage/downsized/',
                                   'STMAARTEN/182b_CubeImage/downsized/',
                                   'STMAARTEN/183a_CubeImage/downsized/',
                                   'STMAARTEN/183b_CubeImage/downsized/',
                                   'STMAARTEN/184a_CubeImage/downsized/',
                                   'STMAARTEN/184b_CubeImage/downsized/',
                                   'STMAARTEN/185_CubeImage/downsized/',
                                   'STMAARTEN/186a_CubeImage/downsized/',
                                   'STMAARTEN/186b_CubeImage/downsized/',
                                   'STMAARTEN/187a_CubeImage/downsized/',
                                   'STMAARTEN/187b_CubeImage/downsized/',
                                   'STMAARTEN/188a_CubeImage/downsized/',
                                   'STMAARTEN/188b_CubeImage/downsized/',
                                   'STMAARTEN/188c_CubeImage/downsized/'])

# Parameters for creating ML-ready labels from images and CVAT annotations
label_params = dict(img_head_dir=op.join(os.environ['EXT_DATA_DIR'], 'housing_passports/data/streetview'),
                    xml_dir=op.join(os.environ['EXT_DATA_DIR'], 'housing_passports/cvat'),
#                    xml_fnames=['4_Door - garage - window - disaster mitigation (Right images) - Lima.xml',
#                                '14_Door - garage - window - disaster mitigation (Right images) - Cartagena_t.xml',
#                                '19_Door - garage - window - disaster mitigation (Left images) - Neiva.xml',
#                                '10_Door - garage - window - disaster mitigation (Left images) - St. Maarten.xml',
#                                '2_Door - garage - window - disaster mitigation (Left images) - Lima.xml',
#                                '13_Door - garage - window - disaster mitigation (Left images) - Cartagena_t.xml',
#                                '20_Door - garage - window - disaster mitigation (Right images) - Neiva.xml',
#                                '23_Door - garage - window - disaster mitigation (Right images) - St. Maarten.xml',
#                                '33_Door - garage - window - disaster mitigation (Left images) - Salina Cruz - Mexico.xml',
#                                '39_Door - garage - window - disaster mitigation (Left images) - Juchitan - Mexico.xml',
#                                '41_Door - garage - window - disaster mitigation (Right images) - Juchitan - Mexico.xml'],
                    xml_fnames=['1_Building classification (Left images) - Lima.xml',
                                '9_Building classification (Left images) - St. Maarten.xml',
                                '24_Building classification (Left images) - St. Maarten.xml',
                                '15_Building classification (Left images) - Cartagena_t.xml',
                                '21_Building classification (Left images) - Neiva.xml',
                                '3_Building classification (Right images) - Lima.xml',
                                '11_Building classification (Right images) - St. Maarten.xml',
                                '16_Building classification (Right images) - Cartagena_t.xml',
                                '22_Building classification (Right images) - Neiva.xml',
                                '35_Building classification (Left images) - Salina Cruz - Mexico.xml',
                                '38_Building classification (Left images) - Juchitan - Mexico.xml',
                                '40_Building classification (Right images) - Juchitan - Mexico.xml'],
                    text_label_dirname='labels_properties',  # Directory name for text file labels
                    tf_output_dir=op.join(os.environ['EXT_DATA_DIR'], 'housing_passports/tf_records_v2'),  # Directory for TFRecords files
                    multilabel_properties=whole_building_properties, # Only set for multilabel case (with building properties)
                    #multilabel_properties=None,
                    property_map_dict=label_map_dict_whole_building)
                    #property_map_dict=label_map_dict_building_parts)

tf_train_params = dict(tfrecord_dir=op.join(os.environ['EXT_DATA_DIR'], 'housing_passports/tf_records_v2'),
                       parts={'train_fnames': ['4_Door - garage - window - disaster mitigation (Right images) - Lima.tfrecord',
                                               '14_Door - garage - window - disaster mitigation (Right images) - Cartagena_t.tfrecord',
                                               '19_Door - garage - window - disaster mitigation (Left images) - Neiva.tfrecord',
                                               '10_Door - garage - window - disaster mitigation (Left images) - St. Maarten.tfrecord'],
                              'val_fnames': ['2_Door - garage - window - disaster mitigation (Left images) - Lima.tfrecord',
                                             '13_Door - garage - window - disaster mitigation (Left images) - Cartagena_t.tfrecord',
                                             '20_Door - garage - window - disaster mitigation (Right images) - Neiva.tfrecord',
                                             '23_Door - garage - window - disaster mitigation (Right images) - St. Maarten.tfrecord']},
                       properties={'train_fnames': ['1_Building classification (Left images) - Lima.tfrecord',
                                                    '9_Building classification (Left images) - St. Maarten.tfrecord',
                                                    '24_Building classification (Left images) - St. Maarten.tfrecord',  # Two training sets only for St. Maarten
                                                    '15_Building classification (Left images) - Cartagena_t.tfrecord',
                                                    '21_Building classification (Left images) - Neiva.tfrecord'],
                                   'val_fnames': ['3_Building classification (Right images) - Lima.tfrecord',
                                                  '11_Building classification (Right images) - St. Maarten.tfrecord',
                                                  '16_Building classification (Right images) - Cartagena_t.tfrecord',
                                                  '22_Building classification (Right images) - Neiva.tfrecord']})
