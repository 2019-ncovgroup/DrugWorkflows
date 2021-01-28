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

space="$space"$(printf "+-%-30s-+-%-25s-+-%10s-+-%8s-----+-%5s-" "------------------------------" "-------------------------" "----------" "---------" "-----")
space="$space"$(printf "+-%10s"    "-----------")
space="$space"$(printf "+-%19s"    "--------------------")
space="$space"$(printf "+-%9s"     "----------")
space="$space"$(printf "+-%10s"    "-----------")
space="$space"$(printf "+-%10s"    "-----------")
space="$space"$(printf "+-%10s+"  "-----------")
echo "$space"

head="$head"$(printf  "| %-30s | %-25s | %10s | %8s      | %5s" "receptor" "smiles" "pilot id" "job id" "nodes")
head="$head"$(printf " | %10s"    "todo")
head="$head"$(printf " | %19s"    "done         ")
head="$head"$(printf " | %9s"     "rate   ")
head="$head"$(printf " | %10s"    "runtime")
head="$head"$(printf " | %10s"    "estimate")
head="$head"$(printf " | %10s |"  "remaining")
echo "$head"
echo "$space"

sum=0
for p in pilot.*; do

    u0=$(ls -d $p/master.*/ | head -n 1 | cut -f 2 -d /)

    stats=""

    if test -f "$p/stats.cache"
    then
        cat "$p/stats.cache"
        continue
    fi

    check=$(ls $p/$u0/$u0.out 2>/dev/null)
    slurmid=$(grep SLURM_JOB_ID $p/env.orig 2>/dev/null | cut -f 2 -d '"')
    nodes=$(grep SLURM_NNODES $p/env.orig 2>/dev/null | cut -f 2 -d '"')

    if test -z "$slurmid"
    then
        slurmid='?'
        state="W"
    else
        state=$(squeue -h --job $slurmid 2>/dev/null | xargs echo | cut -f 5 -d ' ')
    fi

    if test -z "$(ls $p/$u0/wf0.cfg 2>/dev/null)"
    then
        stats="$stats"$(printf  "| %-30s | %-25s | %10s | %8s [%2s] | %5d " "$rec_name" "$smiles" $p $slurmid "$state" $nodes)
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s         "   '')
        stats="$stats"$(printf " | %6s   "          '')
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s"   '')
        stats="$stats"$(printf " | %10s |" '')
        echo "$stats" | tee "$p/stats.cache"
        echo "$stats"
        continue
    fi

    receptor=$(grep '"receptor"' $p/$u0/wf0.cfg | head -n 1 | cut -f 4 -d '"')
    smiles=$(grep   '"smiles"'   $p/$u0/wf0.cfg | head -n 1 | cut -f 4 -d '"')
    name=$(grep     '"name"'     $p/$u0/wf0.cfg | head -n 1 | cut -f 4 -d '"')

    rec_name=$(echo $receptor | cut -c 1-30)
    smi_name=$(echo $smiles   | cut -c 1-25)

    if test -z "$check"
    then
        stats="$stats"$(printf  "| %-30s | %-25s | %10s | %8s [%2s] | %5d" "$rec_name" "$smi_name" $p $slurmid "$state" $nodes)
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s         "   '')
        stats="$stats"$(printf " | %6s   "          '')
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s"   '')
        stats="$stats"$(printf " | %10s |" '')
        printf "$stats\n"
        continue
    fi

    if ! test -f $p/nsmiles
    then
        if test -f $p/$u0/new.idx
        then
            # all 'new.idx' files are the same
            cat $p/$u0/new.idx | wc -l > $p/nsmiles
        else
            stats="$stats"$(printf  "| %-30s | %-25s | %10s | %8s [%2s] | %5d" "$rec_name" "$smi_name" $p $slurmid "$state" $nodes)
            stats="$stats"$(printf " | %10s"            '')
            stats="$stats"$(printf " | %10s         "   '')
            stats="$stats"$(printf " | %6s   "          '')
            stats="$stats"$(printf " | %10s"            '')
            stats="$stats"$(printf " | %10s"   '')
            stats="$stats"$(printf " | %10s |" '')
            printf "$stats\n"
            continue
        fi
    fi
    nsmiles=$(cat $p/nsmiles)
    nsmiles=$((nsmiles - 1))
    count=$(for f in $p/un*/un*.out; do cat $f; done | grep 'result_cb request' | wc -l)

    if test "$count" -eq "0"
    then
        stats="$stats"$(printf  "| %-30s | %-25s | %10s | %8s [%2s] | %5d" "$rec_name" "$smi_name" $p $slurmid "$state" $nodes)
        stats="$stats"$(printf "%10d" $nsmiles)
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s         "   '')
        stats="$stats"$(printf " | %6s   "          '')
        stats="$stats"$(printf " | %10s"            '')
        stats="$stats"$(printf " | %10s"   '')
        stats="$stats"$(printf " | %10s |" '')
        printf "$stats\n"
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
    
    skip="                                          "
    stats="$stats"$(printf  "| %-30s | %-25s | %10s | %8s [%2s] | %5d" "$rec_name" "$smi_name" $p $slurmid "$state" $nodes)
    stats="$stats"$(printf " | %10d"              $nsmiles)
    stats="$stats"$(printf " | %10d [%5.1f%%]"    $count $part)
    stats="$stats"$(printf " | %6.1f /s"          $(calc "$count / $run"))
    stats="$stats"$(printf " | %10s"              $(time_fmt $run))
    if test -z "$state"
    then
        stats="$stats"$(printf " | %10s"   '')
        stats="$stats"$(printf " | %10s |" '')
        echo "$stats" | tee "$p/stats.cache"
    else
        stats="$stats"$(printf " | %10s" $(time_fmt $est))
        stats="$stats"$(printf " | %10s |" $(time_fmt $rem))
        rate=$(calc "$count / $run")
        sum=$(calc "$sum + $rate")
        echo "$stats"
    fi

done

echo "$space"
printf "| %-130s | %6.1f /s | %36s |\n"  "total" "$sum" " "
echo "$space"
echo $(date +%s) $sum >> total
~/alloc.sh
echo


