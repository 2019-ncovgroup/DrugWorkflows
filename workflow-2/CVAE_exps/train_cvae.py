import os, sys, errno
import argparse 
from cvae.CVAE import run_cvae  
import numpy as np 


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--h5_file", dest="f", default='cvae_input.h5', help="Input: contact map h5 file")
# parser.add_argument("-o", help="output: cvae weight file. (Keras cannot load model directly, will check again...)")
parser.add_argument("-d", "--dim", default=3, help="Number of dimensions in latent space")
parser.add_argument("-b", "--batch", default=128, help="Batch size for cvae training") 
parser.add_argument("-gpu", default=0, help="gpu_id")

args = parser.parse_args()

cvae_input = args.f
hyper_dim = int(args.dim) 
gpu_id = args.gpu
batch_size = int(args.batch)

if not os.path.exists(cvae_input):
    raise IOError('Input file doesn\'t exist...')


if __name__ == '__main__': 
    cvae = run_cvae(gpu_id, cvae_input, hyper_dim=hyper_dim, batch_size=batch_size)

    model_weight = 'cvae_weight.h5' 
    model_file = 'cvae_model.h5' 
    loss_file = 'loss.npy' 

    cvae.model.save_weights(model_weight)
    cvae.save(model_file)
    np.save(loss_file, cvae.history.losses) 
