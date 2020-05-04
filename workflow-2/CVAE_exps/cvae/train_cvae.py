import os, sys, errno
import argparse 
from CVAE import run_cvae, run_cvae_tfrecords
import tensorflow as tf


parser = argparse.ArgumentParser()
#parser.add_argument("-f", default='cvae_input.h5', help="Input: contact map h5 file")

#parser.add_argument("-f", default=None, help="Input: contact map h5 file")
parser.add_argument("-f", default=None, help="Input: contact map tfrecordsfile")
# parser.add_argument("-o", help="output: cvae weight file. (Keras cannot load model directly, will check again...)")
parser.add_argument("-d", "--dim", default=3, help="Number of dimensions in latent space") 
parser.add_argument("-gpu", default=0, help="gpu_id")
parser.add_argument(
            "-b", "--batch_size", default=1000,
                help="Batch size for CVAE training")
parser.add_argument(
            "-n", "--num_frame", default="all",
                help="Number of frames used for training")
parser.add_argument(
            "-e", "--epochs", default=100,
                help="Number of epochs for CVAE training")
args = parser.parse_args()

print(args.f, args.dim, args.gpu)

cvae_input = args.f
hyper_dim = args.dim 
gpu_id = args.gpu 
epochs = int(args.epochs)
batch_size = int(args.batch_size)

#if not os.path.exists(cvae_input):
#raise IOError('Input file doesn\'t exist...') 

if __name__ == '__main__': 
    #cvae = run_cvae(gpu_id, cvae_input, hyper_dim=hyper_dim)
    cvae = run_cvae_tfrecords(gpu_id, cvae_input, hyper_dim=hyper_dim,  epochs=epochs, batch_size=batch_size)

    odel_dir = "."
    model_weight = os.path.join(model_dir, 'cvae_weight.h5')
    model_file = os.path.join(model_dir, 'cvae_model.h5')

    cvae.model.save_weights(model_weight)
    cvae.save(model_file)
