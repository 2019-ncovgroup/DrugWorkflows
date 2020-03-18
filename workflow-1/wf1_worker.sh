#!/bin/bash

exec 3>&1 4>&2 >./log 2>&1

conda=$1    ; shift
work=$1     ; shift

env > env_1
set -x
. $conda/etc/profile.d/conda.sh
conda activate covid-19-1
set +x
env > env_2

which python
python -c 'import numpy; print(numpy.__file__)'

while true
do
    active=

    # try to find a mmgbsa candidate
    echo "=   check $work/work_mmgbsa/*"
    ls -d $work/work_mmgbsa/*

    rank=''
    for f in $(ls -d $work/work_mmgbsa/* 2>/dev/null)
    do
        echo "=   mmgbsa   claim  $f"
        rank=$(basename $f)
        mv $f $work/work_mmgbsa_active/$rank
        if test $? = 0
        then
            echo "=   mmgbsa   action $f"
            active=1
            # we own ths rank now
            ./wf1_task.sh $conda $work mmgbsa $work/work_mmgbsa_active/$rank
            echo "=   minimize result: $?"
            rm $work/work_mmgbsa_active/$rank
        fi
    done

    # if we do not find any mmgbsa rank anymore, check for minimization
    echo "=   check $work/work_minimize/*"
    ls -d $work/work_minimize/*

    rank=''
    for f in $(ls -d $work/work_minimize/* 2>/dev/null)
    do
        echo "=   minimize claim  $f"
        rank=$(basename $f)
        mv -v $f $work/work_minimize_active/$rank
        if test $? = 0
        then
            echo "=   minimize action $f"
            active=2
            # we own ths rank now
            ./wf1_task.sh $conda $work minimize $work/work_minimize_active/$rank
            if test $? = 0
            then
                echo "=   minimize result: mmgbsa"
                mv $work/work_minimize_active/$rank $work/work_mmgbsa/$rank
            else
                echo "=   minimize result: negative"
                rm $work/work_minimize_active/$rank
            fi
        else
            echo "=   failed: mv -v $f $work/work_minimize_active/$rank"
        fi
    done

    # if we found neither then all ranks are done and we finish
    test -z $active && break

    echo "=   cont ($active)"

done

echo "=   done ($active)"

