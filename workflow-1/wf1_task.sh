#!/bin/bash

conda=$1 ; shift
work=$1  ; shift
mode=$1  ; shift
rank=$1  ; shift

. $conda/etc/profile.d/conda.sh
conda activate covid-19-1

if test $mode = 'minimize'
then
    echo "==  python ./wf1_task.py minimize $work $rank"
    python ./wf1_task.py minimize $work $rank
    if test $? == 0
    then
        # energy <= 0, prepare for mmgbsa
        echo "==  ok"
        mv -v $rank $work/work_mmgbsa
    else
        echo "==  failed"
        rm -v $rank
    fi

elif test $mode = 'mmgbsa'
then
    echo "==  python ./wf1_task.py minimize $work $rank"
    python ./wf1_task.py minimize $work $rank
    rm -v $rank

fi

