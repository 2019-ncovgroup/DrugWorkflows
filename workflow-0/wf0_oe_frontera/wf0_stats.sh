#!/bin/sh

unset $(env | grep LC | cut -f 1 -d = | grep LC)

echo

time_fmt(){
    sec=$(printf "%.0f" $1)
    min=$((sec / 60))
    hrs=$((min / 60))
    rsec=$((sec - min * 60))
    rmin=$((min - hrs * 60))
    printf "%5d:%02d:%02d" $hrs $rmin $rsec
}

calc(){
    args="$*"
    python -c "print(eval('$args'))"
}


sum=0
for p in pilot.*; do

    if test -f "$p/stats.cache"
    then
        cat "$p/stats.cache"
        continue
    fi

    check=$(ls $p/unit.*/STDOUT 2>/dev/null)
    slurmid=$(grep SLURM_JOB_ID $p/env.orig 2>/dev/null | cut -f 2 -d '"')

    state=$(squeue -h --job $slurmid 2>/dev/null | xargs echo | cut -f 5 -d ' ')
    test -z "$state" && state='?'

    if test -z "$(ls $p/unit.*/wf0.cfg 2>/dev/null)"
    then
        printf "%-50s [%10s] [%6s] new\n" '' $p $slurmid
        continue
    fi

    receptor=$(grep '"receptor"' $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')
    smiles=$(grep   '"smiles"'   $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')
    name=$(grep     '"name"'     $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')

    name=$(echo $name | sed -e 's/_-_/  /g')


    if test -z "$check"
    then
        printf "%-50s %10s %6s waiting\n" "$name" $p $slurmid
        continue
    fi

    if ! test -f $p/nsmiles
    then
        if test -f $p/unit.*/new.idx
        then
            wc  -l $p/unit.*/new.idx | cut -f 1 -d ' ' > $p/nsmiles
        else
            printf "%-50s %10s %6s starting\n" "$name" $p $slurmid
            continue
        fi
    fi
    nsmiles=$(cat $p/nsmiles)
    nsmiles=$((nsmiles - 1))
    count=$(grep 'result_cb request' $p/un*/*OUT | wc -l)

    if test "$count" -eq "0"
    then
        printf "%-50s %10s %6s started\n" "$name" $p $slurmid
        continue
    fi

    now=$(date +%s)
    start=$(cat $p/un*/un*prof | grep cu_exec_start | cut -f 1 -d , | sort -n | head -n 1)
    stop=$( cat $p/un*/un*prof | grep cu_exec_stop  | cut -f 1 -d , | sort -n | tail -n 1)

    test -z "$stop" && stop=$now
    
    run=$( calc "$stop  - $start"        )
    rate=$(calc "$count / $run"          )
    part=$(calc "$count / $nsmiles * 100")
    est=$( calc "$run   / $part    * 100")
    rem=$( calc "$est   - $run"          )
    
    stats=""
    skip="                                          "
    stats="$stats"$(printf "%-50s %10s %6s %2s" "$name" $p $slurmid $state)
    stats="$stats"$(printf "   smi: %10d"              $nsmiles)
    stats="$stats"$(printf        " %10d [%5.1f%%]"    $count $part)
    stats="$stats"$(printf "   rate: %6.1f /s"         $(calc "$count / $run"))
    stats="$stats"$(printf "   run: %10s"              $(time_fmt $run))
    if test "$rem" = 0
    then
        echo "$stats" | tee "$p/stats.cache"
    else
        stats="$stats"$(printf "   est: %13s"          $(time_fmt $est))
        stats="$stats"$(printf "   rem: %13s"          $(time_fmt $rem))
        rate=$(calc "$count / $run")
        sum=$(calc "$sum + $rate")
        echo "$stats"
    fi

done

echo
printf "total rate: %10.1f\n" $sum
echo $sum >> total

