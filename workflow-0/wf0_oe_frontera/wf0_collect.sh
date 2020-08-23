#!/bin/sh

echo
echo "do you really want to collect now?"
echo
read x
test "$x" = 'y' || exit

base="/scratch1/07305/rpilot/workflow-0-results"
for p in pilot.*; do

    name=$(grep '"name"' $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')
    smi=$(echo $name | sed -e 's/_-_/ /g' | cut -f 2 -d ' ')
    dir="$base/$smi"
    sdf="$dir/$name.sdf"
    idx="$dir/$name.idx"

    mkdir -p   $dir
    chmod 0755 $dir

    touch      $sdf 
    touch      $idx

    chmod a+r  $sdf
    chmod a+r  $idx

    printf "%-10s: %30s  " "$p" "$name"

    stop=$(cat $p/unit.*/un*prof | grep 'cu_exec_stop')
    if test -z "$stop" 
    then
        echo 'running'
        continue
    fi

    echo "collect"

    for f in $p/un*/worker.0*/*sdf
    do
        echo "  collect $f"
        cat $f >> $sdf
    done
   
    grep result_cb $p/un*/STDOUT | cut -f 2 -d '.' | cut -f 1 -d ':' >> $idx
   
done

