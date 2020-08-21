#!/bin/sh

total=$1
sum=0
for p in pilot.*; do

    check=$(ls $p/unit.*/STDOUT 2>/dev/null)
    slurmid=$(grep SLURM_JOB_ID $p/env.orig | cut -f 2 -d '"')

    if test -z "$check"
    then
        receptor=$(grep receptor $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')
        printf          "\n"
        printf "receptor:    %10s\n"           $receptor

    else
        receptor=$(grep receptor $p/unit.*/wf0.cfg | head -n 1 | cut -f 4 -d '"')
        count=$(grep 'result_cb request' $p/un*/*OUT | wc -l)
        now=$(date +%s)
        start=$(cat $p/un*/un*prof | grep cu_exec_start | cut -f 1 -d , | sort -n | head -n 1)
        stop=$( cat $p/un*/un*prof | grep cu_exec_stop  | cut -f 1 -d , | sort -n | tail -n 1)
        
        test -z "$total" && total=6700000
        test -z "$stop"  && stop=$now
        
        run=$( echo "$stop  - $start"       | bc -l)
        rate=$(echo "$count / $run"         | bc -l)
        part=$(echo "$count / $total * 100" | bc -l)
        est=$( echo "$run   / $part  * 100" | bc -l)
        rem=$( echo "$est   - $run"         | bc -l)
        
        skip="                                          "
        printf "receptor:    %-30s"                  $receptor
        printf "smiles  :    %10d"                   $total
        printf                "    %10d [%5.1f%%]"   $((total - count)) $(echo "100 - $part" | bc -l)
        printf                "    %10d [%5.1f%%]\n" $count $part
        printf "             %-10s  %8s          "   $p $slurmid
        printf       "rate    :    %10.1f /sec"      $(echo "$count / $run"           | bc -l)
        printf                "    %10.1f /min"      $(echo "$count / $run * 60"      | bc -l)
        printf                "    %10.1f /hrs\n"    $(echo "$count / $run * 60 * 60" | bc -l)
        printf "$skip runtime :    %10.1f  sec"      $(echo "$run"                    | bc -l)
        printf                "    %10.1f  min"      $(echo "$run          / 60"      | bc -l)
        printf                "    %10.1f  hrs\n"    $(echo "$run          / 60 / 60" | bc -l)
        if ! test "$rem" = 0
        then
            printf "$skip estimate:    %10.1f  sec"      $(echo "$est"                    | bc -l)
            printf                "    %10.1f  min"      $(echo "$est          / 60"      | bc -l)
            printf                "    %10.1f  hrs\n"    $(echo "$est          / 60 / 60" | bc -l)
            printf "$skip remain  :    %10.1f  sec"      $(echo "$rem"                    | bc -l)
            printf                "    %10.1f  min"      $(echo "$rem          / 60"      | bc -l)
            printf                "    %10.1f  hrs\n"    $(echo "$rem          / 60 / 60" | bc -l)
            rate=$(echo "$count / $run" | bc -l)
            sum=$(echo "$sum + $rate"   | bc -l)
        fi

    fi

done
printf "total rate: %10.1f\n" $sum

