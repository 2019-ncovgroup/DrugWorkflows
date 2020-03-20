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

if test "$smi_per_task" -ne "0"
then
    idx=$idx_start
    cnt=0
    while test $cnt -le $smi_per_task
    do
        echo $idx
        idx=$((idx + 1))
        cnt=$((cnt + 1))
    done | xargs -t -n 1 -P $cpn -I{} ./smi.sh $conda_dir $smi_fname $tgt_fname {}

else

    sidx=$uid
    spec=$(head -n $((sidx+1)) specfile | tail -n 1 | xargs echo)
    while ! test -z "$spec"
    do
        spec=$(echo $spec | tr -d ':[][:alpha:]')
        echo spec $spec 1>&2
        idx_0=$(echo $spec | cut -f 1 -d ' ')
        idx_1=$(echo $spec | cut -f 3 -d ' ')
        idx=$idx_0
        while test $idx -le $idx_1
        do
            echo $idx
            idx=$((idx+1))
        done
        old=$spec
        sidx=$((sidx + $uids))
        spec=$(head -n $((sidx+1)) specfile | tail -n 1 | xargs echo)
        test "$spec" = "$old" && break
  # done | xargs -t -n 1 -P $cpn -I{} true ./smi.sh $conda_dir $smi_fname $tgt_fname {}
    done | xargs -t -n 1 -P $cpn -I{} ./smi.sh $conda_dir $smi_fname $tgt_fname {}
fi




