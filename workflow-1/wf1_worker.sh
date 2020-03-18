#!/bin/bash

eval "$prof"
prof app_start

conda=$1    ; shift
work=$1     ; shift

unset CONDA_SHLVL
unset CONDA_PROMPT_MODIFIER
unset CONDA_EXE
unset _CE_CONDA
unset CONDA_PREFIX_1
unset CONDA_PREFIX
unset CONDA_PYTHON_EXE
unset CONDA_DEFAULT_ENV

. $conda/etc/profile.d/conda.sh
conda activate covid-19-1

while true
do
    active=

    # try to find a mmgbsa candidate
    echo "=   check $work/work_mmgbsa/*"

    rank=''
    for f in $(ls -d $work/work_mmgbsa/* 2>/dev/null)
    do
        # ---------------------------------------------------------
        # NOTE: we don't do mmbgsa right now
        break
        # ---------------------------------------------------------


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

            # do *NOT* break here - we prefer mmbgsa work
        fi
    done

    # if we do not find any mmgbsa rank anymore, check for minimization
    echo "=   check $work/work_minimize/*"

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
            # break so we can switch to mmbgsa again
            break
        else
            echo "=   failed: mv -v $f $work/work_minimize_active/$rank"
            # do not break here, instead try to find some other rank to minimize
        fi
    done

    # if we found neither then all ranks are done and we finish
    test -z $active && break

    echo "=   cont ($active)"

done

prof app_stop
echo "=   done ($active)"

