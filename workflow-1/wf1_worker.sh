#!/bin/bash

conda_dir=$1    ; shift
smi_fname=$1    ; shift
tgt_fname=$1    ; shift
cpn=$1          ; shift
idx_start=$1    ; shift
smi_per_task=$1 ; shift

idx_end=$((idx_start + smi_per_task))

. $conda_dir/etc/profile.d/conda.sh
conda activate covid-19-0

export OE_LICENSE=oe_license.txt

chmod 0755 wf1_task.sh

idx=$idx_start
while test $idx -le $idx_end
do
    echo $idx
    idx=$((idx+1))
done | xargs -t -n 1 -P $cpn -I{} ./wf1_task.sh $conda_dir $smi_fname $tgt_fname {}


