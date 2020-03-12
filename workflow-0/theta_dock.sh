#!/bin/sh

smi_fname=$1 ; shift
tgt_fname=$1 ; shift
idx=$1       ; shift
chunk_size=$1; shift

# frontera
path='/home/merzky/projects/covid/Model-generation/'
conda='/home/merzky/.miniconda3/'

# stampede
path='/home1/01083/tg803521/radical/covid/Model-generation/'
conda='/home1/01083/tg803521/.miniconda3/'

# comet
path='/home/mturilli/github/Model-generation'
conda='/home/mturilli/.miniconda3/'

source $conda/etc/profile.d/conda.sh
conda activate covid-19-0

export OE_LICENSE=oe_license.txt


COMMAND="python ./theta_dock.py $smi_fname $tgt_fname $idx $chunk_size"


function cleanup {
    echo "SIGTERM trap" >&2
    kill %1 %2
}
trap cleanup SIGTERM

($COMMAND; echo "completed" >&2; kill $$) &
(sleep 60; echo "timeout"   >&2; kill $$) &

wait


