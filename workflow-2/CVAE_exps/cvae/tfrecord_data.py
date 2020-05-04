import os
import tensorflow as tf
import numpy as np
# ------------------------------------------------------------------------------
#   Estimator Input function (input_fn)
# ------------------------------------------------------------------------------
import pdb
import json

with open('tfrecords-metadata.json', 'r') as f:
    metadata = json.load(f)

shape0 = metadata['shape0']
shape1 = metadata['shape1']
shape2 = metadata['shape2']
params = {}
params['shape0'] = shape0 
params['shape1'] = shape1 
params['shape2'] = shape2 


def input_fn(batch_size, filename='bytes-train.tfrecords', is_training=True,  params=None):
    """Return dataset iterator."""
    if is_training:
        file_pattern = os.path.join(filename)
    else: 
        filename = filename.replace("-train", "-val")
        file_pattern = os.path.join(filename)

    dataset = tf.data.Dataset.list_files(file_pattern, shuffle=True)
    dataset = dataset.flat_map(tf.data.TFRecordDataset)

    def _parse_record_fn(raw_record):
        """Decode raw TFRecord into feature and label components."""
        feature_map = {
            'data':  tf.io.FixedLenFeature([], dtype=tf.string,  default_value=''),
            #'shape': tf.io.FixedLenFeature([], dtype=tf.string,  default_value=''),
            #'shape0': tf.io.FixedLenFeature([], dtype=tf.float32),# default_value=''),
            #'shape1': tf.io.FixedLenFeature([], dtype=tf.float32),# default_value=''),
            #'shape2': tf.io.FixedLenFeature([], dtype=tf.float32)#, default_value='')
        }
        record_features = tf.io.parse_single_example(raw_record, feature_map)
        data = record_features['data']
        newdata =tf.io.decode_raw(data, tf.uint8)
        newdata = tf.cast(newdata, tf.float32)
        #pdb.set_trace()
        print('NEWDATA',newdata, newdata.shape, newdata.shape.dims[0].value)
        #shape = tf.io.decode_raw(record_features['shape'], tf.int32)
        #shape0 = record_features['shape0']
        #shape0_data = tf.io.decode_raw(shape0, tf.float32)
        #print('SHAPE0', shape0_data.shape, shape0_data.shape.dims[0].value)
        #shape1 = record_features['shape1']
        #shape1_data = tf.io.decode_raw(shape1, tf.float32)
        #shape2 = record_features['shape2']
        #shape2_data = tf.io.decode_raw(shape2, tf.float32)
        #print('SHAPE1', np.asarray(shape0_data))
#        pdb.set_trace()


       # newdata = tf.reshape(newdata, [314, 314, 1])
        newdata = tf.reshape(newdata, [shape0, shape1, shape2])
        #newdata = tf.reshape(newdata, shape)
        return newdata,newdata

    return process_record_dataset(dataset, is_training, batch_size, 1000, _parse_record_fn, num_epochs=1)



def process_record_dataset(dataset, is_training, batch_size, shuffle_buffer, parse_record_fn, num_epochs=None):
    """Given a Dataset with raw records, return an iterator over the records."""

    dataset = dataset.prefetch(buffer_size=batch_size)

    if is_training:
        dataset = dataset.shuffle(buffer_size=shuffle_buffer)
        dataset = dataset.repeat()    # forever, a CS-1 rqmt

    dataset = dataset.apply(
        tf.data.experimental.map_and_batch(
            lambda raw_record: parse_record_fn(raw_record),
            batch_size=batch_size,
            drop_remainder=True))
    
    dataset = dataset.prefetch(buffer_size=batch_size)
    """
    # Create an iterator
    iterator = dataset.make_one_shot_iterator()

    # Create your tf representation of the iterator
    image = iterator.get_next()
    
    # Bring your picture back in shape
    image = tf.reshape(image, [22, 22, 1])
    image = tf.cast(image, dtype=tf.float32)
    
    #Get your datatensors
    image = create_dataset('images.tfrecords')
    return image
    """
    return dataset
