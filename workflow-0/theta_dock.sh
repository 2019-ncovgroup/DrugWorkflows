#!/bin/sh

smi_fname=$1 ; shift
tgt_fname=$1 ; shift
idx=$1       ; shift
chunk_size=$1; shift

path='/home1/01083/tg803521/radical/covid/Model-generation/'
conda='/home1/01083/tg803521/.miniconda3/'

source $conda/etc/profile.d/conda.sh
conda activate covid-19-0

export OE_LICENSE=oe_license.txt

python ./theta_dock.py $smi_fname $tgt_fname $idx $chunk_size


----------------------------------------------------------------------------

