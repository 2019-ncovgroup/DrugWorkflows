#!/bin/bash

# interface theta_dock.py
#input_smiles_file = sys.argv[1]
#target_file       = sys.argv[2]
#start_idx         = int(sys.argv[3])
#n_smiles          = int(sys.argv[4])

conda_dir=$1    ; shift

# local interface
smi_fname=$1    ; shift
tgt_fname=$1    ; shift
idx=$1          ; shift
len=1

. $conda_dir/etc/profile.d/conda.sh
conda activate covid-19-0

export PYTHONPATH=`pwd`:$PYTHONPATH
export CONDA_SHLVL=2
export CONDA_PROMPT_MODIFIER=(covid-19-0)
export CONDA_EXE=/home/mturilli/.miniconda3/bin/conda
export _CE_CONDA=
export CONDA_PREFIX_1=/home/mturilli/.miniconda3
export CONDA_PREFIX=/home/mturilli/.miniconda3/envs/covid-19-0
export CONDA_PYTHON_EXE=/home/mturilli/.miniconda3/bin/python
export CONDA_DEFAULT_ENV=covid-19-0
export PATH=/home/mturilli/.miniconda3/envs/covid-19-0/bin:$PATH

COMMAND="python ./theta_dock.py $smi_fname $tgt_fname $idx $len"

cleanup(){
  # echo "SIGTERM trap" >&2
    kill %1 %2 2>/dev/null
}

trap cleanup TERM

(sleep 60; echo "timeout"   >&2; kill $$        2>/dev/null) & export s_pid=$!
($COMMAND; echo "completed" >&2; kill $$ $s_pid 2>/dev/null) &

wait

