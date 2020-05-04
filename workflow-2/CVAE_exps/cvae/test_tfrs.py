""" TFRecord generation """

import numpy as np
import os
#import pandas as pd
import sys
import tensorflow as tf
import pdb
import json

def convert_to_tfr_1(x, path):
    """ """
    print(f"writing float TFRs to {path}")
    with tf.io.TFRecordWriter(path) as writer:
        for i in range(len(x)):
            #x_curr = x[i].squeeze()
            #x_curr = x_curr.reshape([22 * 22])
            x_curr = x[i]
            x_curr = x_curr.reshape([22*22*1])
            x_list = tf.train.FloatList(value=x_curr)
            x_feature = tf.train.Feature(float_list=x_list)

            feature_dict = {'data': x_feature}

            # create the example and write a TFRecord
            feature_set = tf.train.Features(feature=feature_dict)
            example = tf.train.Example(features=feature_set)
            writer.write(example.SerializeToString())

def convert_to_tfr_2(x, path):
    """ 
    print(f"writing byte TFRs to {path}")
    with tf.io.TFRecordWriter(path) as writer:
        for i in range(len(x)):
            x_curr = x[i]#.squeeze()
            shape0, shape1, shape2 = x_curr.shapei
            x_curr = x_curr.reshape([shape0 * shape1 * shape2])
            ints8 = x_curr.astype(np.int8)
            bytes8 = ints8.tostring()
            bytes8 = bytes(bytes8)
            bytes8_list = tf.train.BytesList(value=[bytes8])
            x_feature = tf.train.Feature(bytes_list=bytes8_list)
            x_curr_shape = np.array(x_curr.shape, np.int32).tobytes()
            x_curr_shape0 = np.array(shape0, np.uint8)
            x_curr_shape1 = np.array(shape1, np.uint8)
            x_curr_shape2 = np.array(shape2, np.uint8)
            shape0_bytes8 = x_curr_shape0.tobytes()
            shape1_bytes8 = x_curr_shape1.tobytes()
            shape2_bytes8 = x_curr_shape2.tobytes()
            shape_feature = tf.train.Feature(bytes_list=tf.train.BytesList(value=[x_curr_shape]))
            shape0_feature = tf.train.Feature(bytes_list=tf.train.BytesList(value=[shape0_bytes8]))
            shape1_feature = tf.train.Feature(bytes_list=tf.train.BytesList(value=[shape1_bytes8]))
            shape2_feature = tf.train.Feature(bytes_list=tf.train.BytesList(value=[shape2_bytes8]))
            
            feature_dict = {'data': x_feature,
                            'shape': shape_feature,
                            'shape0': shape0_feature,
                            'shape1': shape1_feature,
                            'shape2': shape2_feature} 
            #pdb.set_trace()
            # create the example and write a TFRecord
            feature_set = tf.train.Features(feature=feature_dict)
            example = tf.train.Example(features=feature_set)
            writer.write(example.SerializeToString())
            """
    with tf.io.TFRecordWriter(path) as writer:
        for i in range(len(x)):
            x_curr = x[i]#.squeeze()
            shape0, shape1, shape2 = x_curr.shape
            x_curr = x_curr.reshape([shape0 * shape1 * shape2])
                #x_curr = x_curr.reshape([106 * 106 * 1])
            ints8 = x_curr.astype(np.int8)
            bytes8 = ints8.tostring()
            bytes8 = bytes(bytes8)
            bytes8_list = tf.train.BytesList(value=[bytes8])
            x_feature = tf.train.Feature(bytes_list=bytes8_list)

            feature_dict = {'data': x_feature}                                            
                # create the example and write a TFRecord
            feature_set = tf.train.Features(feature=feature_dict)
            example = tf.train.Example(features=feature_set) 
            writer.write(example.SerializeToString())

            metadata = dict(
                    shape0  = int(shape0),
                    shape1  = int(shape1),
                    shape2  = int(shape2)
                    )
    with open('../CVAE_exps/tfrecords-metadata.json', 'w') as f:
        json.dump(metadata, f)
"""
def main():
    array = np.zeros([22,22,1])
    alist = []
    alist.append(array)

    for entry in range(9):
        a = alist[entry].copy()
        for i in range(a.shape[0]):
            for j in range(a.shape[1]):
                a[i, j, 0] = entry + i + j
        alist.append(a)

    convert_to_tfr_1(alist, './test-structured-floats.tfrs')
    convert_to_tfr_2(alist, './test-structured-bytes.tfrs')
    print('done')

#main()
"""
