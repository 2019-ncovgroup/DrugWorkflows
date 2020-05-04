

'''
Convolutional variational autoencoder in Keras;

Reference: "Auto-Encoding Variational Bayes" (https://arxiv.org/abs/1312.6114);
'''
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

import tensorflow as tf
from tensorflow.keras.mixed_precision import experimental as mixed_precision
import numpy as np
from tensorflow.keras.layers import Input, Dense, Lambda, Flatten, Reshape, Dropout
from tensorflow.keras.layers import Convolution2D, Conv2DTranspose
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import SGD, Adam, RMSprop, Adadelta
from tensorflow.keras.callbacks import Callback, ModelCheckpoint
from tensorflow.keras import backend as K
from tensorflow.keras.losses import BinaryCrossentropy 
# from tensorflow.keras import objectives
import warnings

import horovod.tensorflow as hvd
import pdb
from tfrecord_data import input_fn
from test_tfrs import convert_to_tfr_1, convert_to_tfr_2
import sklearn
from sklearn.model_selection import train_test_split
import json

# Initialize Horovod
hvd.init()

# Horovod: pin GPU to be used to process local rank (one GPU per process)

TF_GPU_HOST_MEM_LIMIT_IN_MB=3200000000000
tf.config.experimental.set_lms_enabled(True)
tf.config.experimental.set_lms_defrag_enabled(True)
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)
if gpus:
    print("setting mixed_precision")
    tf.config.experimental.set_visible_devices(gpus[hvd.local_rank()], 'GPU')
    tf.keras.backend.clear_session()
    tf.config.optimizer.set_jit(False) #
    
    policy = mixed_precision.Policy('mixed_float16')
    mixed_precision.set_policy(policy)


#config = tf.compat.v1.ConfigProto()
#config.gpu_options.allow_growth = True
#session = tf.compat.v1.InteractiveSession(config=config)
with open('train_len.json', 'r') as f:
    train_data = json.load(f)
train_len = train_data['train']
params = {}
params['train'] = train_len

# save history from log;
class LossHistory(Callback):
    def on_train_begin(self, logs={}):
        self.losses = []
        self.val_losses = []

    def on_epoch_end(self, epoch, logs={}):
        self.losses.append(logs.get("loss"))
        self.val_losses.append(logs.get("val_loss"))


class conv_variational_autoencoder(object):
    '''
    variational autoencoder class;

    parameters:
      - image_size: tuple;
        height and width of images;
      - channels: int;
        number of channels in input images;
      - conv_layers: int;
        number of encoding/decoding convolutional layers;
      - feature_maps: list of ints;
        number of output feature maps for each convolutional layer;
      - filter_shapes: list of tuples;
        convolutional filter shape for each convolutional layer;
      - strides: list of tuples;
        convolutional stride for each convolutional layer;
      - dense_layers: int;
        number of encoding/decoding dense layers;
      - dense_neurons: list of ints;
        number of neurons for each dense layer;
      - dense_dropouts: list of float;
        fraction of neurons to drop in each dense layer (between 0 and 1);
      - latent_dim: int;
        number of dimensions for latent embedding;
      - activation: string (default='relu');
        activation function to use for layers;
      - eps_mean: float (default = 0.0);
        mean to use for epsilon (target distribution for embedding);
      - eps_std: float (default = 1.0);
        standard dev to use for epsilon (target distribution for embedding);

    methods:
      - train(data,batch_size,epochs=1,checkpoint=False,filepath=None);
        train network on given data;
      - save(filepath);
        save the model weights to a file;
      - load(filepath);
        load model weights from a file;
      - return_embeddings(data);
        return the embeddings for given data;
      - generate(embedding);
        return a generated output given a latent embedding;
    '''

    def __init__(self, image_size, channels, conv_layers, feature_maps, 
                 filter_shapes, strides, dense_layers, dense_neurons, 
                 dense_dropouts, latent_dim, activation='relu', 
                 eps_mean=0.0, eps_std=1.0):

        self.history = LossHistory()

        # check that arguments are proper length;
        if len(filter_shapes) != conv_layers:
            raise Exception(
                "number of convolutional layers must equal length of filter_shapes list")
        if len(strides) != conv_layers:
            raise Exception(
                "number of convolutional layers must equal length of strides list")
        if len(feature_maps) != conv_layers:
            raise Exception(
                "number of convolutional layers must equal length of feature_maps list")
        if len(dense_neurons) != dense_layers:
            raise Exception(
                "number of dense layers must equal length of dense_neurons list")
        if len(dense_dropouts) != dense_layers:
            raise Exception(
                "number of dense layers must equal length of dense_dropouts list")

        # even shaped filters may cause problems in theano backend;
        even_filters = [
            f for pair in filter_shapes for f in pair if f % 2 == 0]
        if K.image_data_format() == 'th' and len(even_filters) > 0:
            warnings.warn(
                'Even shaped filters may cause problems in Theano backend')
        if K.image_data_format() == 'channels_first' and len(even_filters) > 0:
            warnings.warn(
                'Even shaped filters may cause problems in Theano backend')

        self.eps_mean = eps_mean
        self.eps_std = eps_std
        self.image_size = image_size

        # define input layer;
        if K.image_data_format() == 'th' or K.image_data_format() == 'channels_first':
            self.input = Input(shape=(channels, image_size[0], image_size[1]))
        else:
            self.input = Input(shape=(image_size[0], image_size[1], channels))

        # define convolutional encoding layers;
        self.encode_conv = []
        layer = Convolution2D(
            feature_maps[0], filter_shapes[0], padding='same',
            activation=activation, strides=strides[0])(self.input)
        self.encode_conv.append(layer)
        for i in range(1, conv_layers):
            layer = Convolution2D(feature_maps[i], filter_shapes[i],
                                  padding='same', activation=activation,
                                  strides=strides[i])(self.encode_conv[i - 1])
            self.encode_conv.append(layer)

        # define dense encoding layers;
        self.flat = Flatten()(self.encode_conv[-1])
        self.encode_dense = []
        layer = Dense(dense_neurons[0], activation=activation)(
            Dropout(dense_dropouts[0])(self.flat))
        self.encode_dense.append(layer)
        for i in range(1, dense_layers):
            layer = Dense(dense_neurons[i], activation=activation)(
                Dropout(dense_dropouts[i])(self.encode_dense[i - 1]))
            self.encode_dense.append(layer)

        # define embedding layer;
        
        self.z_mean = Dense(latent_dim, dtype=tf.float32)(self.encode_dense[-1])
        self.z_log_var = Dense(latent_dim, dtype=tf.float32)(self.encode_dense[-1])
        self.z = Lambda(self._sampling, output_shape=(
            latent_dim,))([self.z_mean, self.z_log_var])
        
        # save all decoding layers for generation model;
        self.all_decoding = []

        # define dense decoding layers;
        self.decode_dense = []
        layer = Dense(dense_neurons[-1], activation=activation)
        self.all_decoding.append(layer)
        self.decode_dense.append(layer(self.z))
        for i in range(1, dense_layers):
            layer = Dense(dense_neurons[-i - 1], activation=activation)
            self.all_decoding.append(layer)
            self.decode_dense.append(layer(self.decode_dense[i - 1]))

        # dummy model to get image size after encoding convolutions;
        self.decode_conv = []
        if K.image_data_format() == 'th' or K.image_data_format() == 'channels_first':
            dummy_input = np.ones((1, channels, image_size[0], image_size[1]))
        else:
            dummy_input = np.ones((1, image_size[0], image_size[1], channels))
        dummy = Model(self.input, self.encode_conv[-1])
        conv_size = dummy.predict(dummy_input).shape
        layer = Dense(conv_size[1] * conv_size[2] *
                      conv_size[3], activation=activation)
        self.all_decoding.append(layer)
        self.decode_dense.append(layer(self.decode_dense[-1]))
        reshape = Reshape(conv_size[1:])
        self.all_decoding.append(reshape)
        self.decode_conv.append(reshape(self.decode_dense[-1]))

        # define deconvolutional decoding layers;
        for i in range(1, conv_layers):
            if K.image_data_format() == 'th' or K.image_data_format() == 'channels_first':
                dummy_input = np.ones(
                    (1, channels, image_size[0], image_size[1]))
            else:
                dummy_input = np.ones(
                    (1, image_size[0], image_size[1], channels))
            dummy = Model(self.input, self.encode_conv[-i - 1])
            conv_size = list(dummy.predict(dummy_input).shape)

            if K.image_data_format() == 'th' or K.image_data_format() == 'channels_first':
                conv_size[1] = feature_maps[-i]
            else:
                conv_size[3] = feature_maps[-i]


            layer = Conv2DTranspose(feature_maps[-i - 1], filter_shapes[-i],
                                        padding='same', activation=activation,
                                        strides=strides[-i])
            self.all_decoding.append(layer)

            self.decode_conv.append(layer(self.decode_conv[i - 1]))

        layer = Conv2DTranspose(channels, filter_shapes[0], padding='same',
                                activation='sigmoid', strides=strides[0])
        self.all_decoding.append(layer)
        layer = Conv2DTranspose(channels, filter_shapes[0], padding='same',
                                activation='sigmoid', strides=strides[0], dtype='float32')
        self.output = layer(self.decode_conv[-1])

        # build model;
        self.model = Model(self.input, self.output)
        print(self.model.predict(dummy_input).shape)

        #Adam
        lr_scaler = hvd.size()
        self.optimizer = Adam(lr=0.001 * lr_scaler, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=True)

        #SGD optimizer
        #self.optimizer = SGD(lr=0.001,  nesterov=True)

        #RMSProp optimizer
        #self.optimizer = RMSprop(lr=0.001, rho=0.9, epsilon=1e-08, decay=0.0)
        
        # Add Horovod Distributed Optimize
        self.optimizer = hvd.DistributedOptimizer(self.optimizer, op=hvd.Average)
#        tf.train.experimental.enable_mixed_precision_graph_rewrite(
#            self.optimizer, loss_scale='dynamic' )
        self.model.compile(optimizer=self.optimizer, loss=self._vae_loss, 
                           experimental_run_tf_function=False)#, metrics=[kl_loss])
        print("model summary:")
        self.model.summary()

        # model for embeddings;
        self.embedder = Model(self.input, self.z_mean)

        # model for generation;
        self.decoder_input = Input(shape=(latent_dim,))
        self.generation = []
        self.generation.append(self.all_decoding[0](self.decoder_input))
        for i in range(1, len(self.all_decoding)):
            self.generation.append(
                self.all_decoding[i](self.generation[i - 1]))
        self.generator = Model(self.decoder_input, self.generation[-1])

    def _sampling(self, args):
        '''     
        sampling function for embedding layer;
        '''
        z_mean, z_log_var = args
        print('THIS IS FROM SAMPLING', z_mean.dtype, z_log_var.dtype)
        epsilon = K.random_normal(shape=K.shape(z_mean), mean=self.eps_mean,
                                 stddev=self.eps_std, dtype='float16')
        return tf.dtypes.cast(z_mean + K.exp(z_log_var) * epsilon, tf.float32)
        
    def _vae_loss(self, input, output):
        '''
        loss function for variational autoencoder;
        '''
        input_flat = K.flatten(input)
        output_flat = K.flatten(output)
        # print input.shape, output.shape
        bce = BinaryCrossentropy()
        bincros= bce(input_flat, output_flat)
        xent_loss = self.image_size[0] * self.image_size[1] * \
            bincros
        kl_loss = -0.5 * K.mean(
            1 + self.z_log_var - K.square(self.z_mean) -
            K.exp(self.z_log_var), axis=-1)
        
        return xent_loss + kl_loss
    

    def set_tfrecords(self, filename):
        self.tfrecords_train = filename
        self.tfrecords_val = filename.replace("-train", "-val")


    def train(self, data, batch_size, epochs=1, validation_data=None,
              checkpoint=False, filepath=None):
        '''
        train network on given data;

        parameters:
          - data: numpy array;
            input data;
          - batch_size: int;
            number of records per batch;
          - epochs: int (default: 1);
            number of epochs to train for;
          - validation_data: tuple (optional);
            tuple of numpy arrays (X,y) representing validation data;
          - checkpoint: boolean (default: False);
            whether or not to save model after each epoch;
          - filepath: string (optional);
            path to save model if checkpoint is set to True;

        outputs:
            None;
        '''
        if checkpoint and filepath is None:
            raise Exception("Please enter a path to save the network") 

        callbacks = [
            # Horovod: broadcast initial variable states from rank 0 to all other processes.
            # This is necessary to ensure consistent initialization of all workers when
            # training is started with random weights or restored from a checkpoint.
            hvd.keras.callbacks.BroadcastGlobalVariablesCallback(0),

            # Horovod: average metrics among workers at the end of every epoch.
            #
            # Note: This callback must be in the list before the ReduceLROnPlateau,
            # TensorBoard or other metrics-based callbacks.
            hvd.keras.callbacks.MetricAverageCallback(),

            # Horovod: using `lr = 1.0 * hvd.size()` from the very beginning leads to worse final
            # accuracy. Scale the learning rate `lr = 1.0` ---> `lr = 1.0 * hvd.size()` during
            # the first three epochs. See https://arxiv.org/abs/1706.02677 for details.
            hvd.keras.callbacks.LearningRateWarmupCallback(warmup_epochs=3, verbose=1),
        ]

        # Horovod: save checkpoints only on worker 0 to prevent other workers from corrupting them.
        if hvd.rank() == 0:
            callbacks.append(tf.keras.callbacks.ModelCheckpoint('./checkpoint-{epoch}.h5', save_weights_only = True))

        # Horovod: write logs on worker 0.
        verbose = 1 if hvd.rank() == 0 else 0


        #self.steps_per_epoch=(len(data)/batch_size)//hvd.size()
        #print((len(data)/batch_size)//hvd.size())
        #print(hvd.size())

        # convert data to tensforflow dataset 

        
#        pdb.set_trace()

        #train_data, val_data = train_test_split(data, test_size=.20, random_state=42)
        #del(data)

        #convert_to_tfr_1(train_data, './float-train.tfrecords') 
       # convert_to_tfr_1(val_data, './float-val.tfrecords')
      
        #convert_to_tfr_2(train_data, './bytes-train-plpro.tfrecords')        
        #del(train_data)
        #convert_to_tfr_2(val_data, './bytes-val-plpro.tfrecords')
        #del(val_data)
     #   pdb.set_trace()
        train_dataset = input_fn(batch_size, filename=self.tfrecords_train, is_training=True, params=None)
        val_dataset = input_fn(batch_size, filename=self.tfrecords_val, is_training=False, params=None)
        
        #self.steps_per_epoch=(len(train_dataset)/batch_size)//hvd.size()
        self.steps_per_epoch=(train_len/batch_size)//hvd.size()
        #pdb.set_trace()

        his = self.model.fit(train_dataset,  
                       steps_per_epoch=self.steps_per_epoch, 
                       epochs=epochs, shuffle=True,
                       validation_data=val_dataset, 
                       callbacks= callbacks)#[self.history] + callbacks) 
        print('\nhistory dict:', his.history)
        history = his.history
        json.dump(str(his.history), open('benchmarks/plpro_%d_%dg_%db_%de.json'%(hvd.rank(), hvd.size(), batch_size,epochs), 'w'))
   
    def save(self, filepath):
        '''
        save the model weights to a file
        parameters:
          - filepath: string
            path to save model weights

        outputs:
            None
        '''
        self.model.save_weights(filepath)

    def load(self, filepath):
        '''
        load model weights from a file

        parameters:
          - filepath: string
            path from which to load model weights

        outputs:
            None
        '''
        self.model.load_weights(filepath)

    def decode(self, data):
        '''
        return the decodings for given data

        parameters:
          - data: numpy array
            input data

        outputs:
            numpy array of decodings for input data
        '''
        return self.model.predict(data)

    def return_embeddings(self, data):
        '''
        return the embeddings for given data

        parameters:
          - data: numpy array
            input data

        outputs:
            numpy array of embeddings for input data
        '''
        return self.embedder.predict(data)

    def generate(self, embedding):
        '''
        return a generated output given a latent embedding

        parameters:
          - data: numpy array
            latent embedding

        outputs:
            numpy array of generated output
        '''
        return self.generator.predict(embedding)


