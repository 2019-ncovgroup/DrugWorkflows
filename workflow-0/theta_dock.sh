#!/bin/bash

conda_dir=$1    ; shift
smi_fname=$1    ; shift
tgt_fname=$1    ; shift
cpn=$1          ; shift
idx_start=$1    ; shift
smi_per_task=$1 ; shift
uid=$1          ; shift
uids=$1         ; shift

. $conda_dir/etc/profile.d/conda.sh
conda activate covid-19-0

export OE_LICENSE=oe_license.txt

chmod 0755 smi.sh

idx=$((idx_start + uid))
cnt=0
while test $cnt -le $smi_per_task
do
    echo $idx
    idx=$((idx + uids))
    cnt=$((cnt + 1))
done | xargs -t -n 1 -P $cpn -I{} ./smi.sh $conda_dir $smi_fname $tgt_fname {}


