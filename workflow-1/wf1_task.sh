#!/bin/bash

conda=$1 ; shift
work=$1  ; shift
mode=$1  ; shift
rank=$1  ; shift

base=$(basename $rank)

eval "$prof"
prof task_start $base

# module reset
# 
# module load xl/16.1.1-5   
# module load spectrum-mpi/10.3.1.2-20200121   
# module load hsi/5.0.2.p5   
# module load xalt/1.2.0   
# module load lsf-tools/2.0   
# module load darshan-runtime/3.1.7   
# module load DefApps   
# module load python/3.7.0-anaconda3-5.3.0
# module load cuda

# . $conda/etc/profile.d/conda.sh
# conda activate covid-19-1

if test $mode = 'minimize'
then
    echo "==  python ./wf1_task.py $work minimize $rank"
    prof minimize_start $base
    python ./wf1_task.py $work minimize $rank
    prof minimize_stop $base
    if test $? == 0
    then
        # energy <= 0, prepare for mmgbsa
        echo "==  ok"
        mv -v $rank $work/work_mmgbsa
    else
        echo "==  failed"
        touch $work/work_stats/$base
        rm -v $rank
    fi

elif test $mode = 'mmgbsa'
then
    echo "==  python ./wf1_task.py $work mmgbsa $rank"
    prof mmgbsa_start $base
    python ./wf1_task.py $work mmgbsa $rank
    prof mmgbsa_stop $base
    touch $work/work_stats/$base
    rm -v $rank

fi

prof task_stop $base

