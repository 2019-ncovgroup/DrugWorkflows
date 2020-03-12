#!/bin/sh

smi_fname=$1    ; shift
tgt_fname=$1    ; shift
idx=$1          ; shift
len=1

COMMAND="echo $smi_fname $tgt_fname $idx $len `date` >> OUTPUT; sleep 10; date >> OUTPUT"
COMMAND="python ./theta_dock.py $smi_fname $tgt_fname $idx $len >> OUTPUT"

cleanup(){
  # echo "SIGTERM trap" >&2
    kill %1 %2 2>/dev/null
}

trap cleanup TERM

(sleep 60; echo "timeout"   >&2; kill $$        2>/dev/null) & export s_pid=$!
($COMMAND; echo "completed" >&2; kill $$ $s_pid 2>/dev/null) &

wait

