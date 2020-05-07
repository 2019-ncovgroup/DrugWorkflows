#!/bin/sh

total=$1
count=$(grep 'result_cb request' un*/*OUT | wc -l)
now=$(date +%s)
start=$(cat un*/un*prof | grep cu_exec_start | cut -f 1 -d , | sort -n | head -n 1)
stop=$( cat un*/un*prof | grep cu_exec_stop  | cut -f 1 -d , | sort -n | tail -n 1)

test -z "$total" && total=6700000
test -z "$stop"  && stop=$now

run=$( echo "$stop  - $start"       | bc -l)
rate=$(echo "$count / $run"         | bc -l)
part=$(echo "$count / $total * 100" | bc -l)
est=$( echo "$run   / $part  * 100" | bc -l)
rem=$( echo "$est   - $run"         | bc -l)

printf "smiles  : %10d\n"           $total
printf "count   : %10d [%4.1f%%]\n" $count $part
printf "rate    : %10.1f /sec\n"    $(echo "$count / $run"           | bc -l)
printf "          %10.1f /min\n"    $(echo "$count / $run * 60"      | bc -l)
printf "          %10.1f /hrs\n"    $(echo "$count / $run * 60 * 60" | bc -l)
printf "runtime : %10.1f sec\n"     $(echo "$run"                    | bc -l)
printf "          %10.1f min\n"     $(echo "$run          / 60"      | bc -l)
printf "          %10.1f hrs\n"     $(echo "$run          / 60 / 60" | bc -l)
printf "estimate: %10.1f sec\n"     $(echo "$est"                    | bc -l)
printf "          %10.1f min\n"     $(echo "$est          / 60"      | bc -l)
printf "          %10.1f hrs\n"     $(echo "$est          / 60 / 60" | bc -l)
printf "remain  : %10.1f sec\n"     $(echo "$rem"                    | bc -l)
printf "          %10.1f min\n"     $(echo "$rem          / 60"      | bc -l)
printf "          %10.1f hrs\n"     $(echo "$rem          / 60 / 60" | bc -l)


