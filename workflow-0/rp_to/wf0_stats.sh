#!/bin/sh

total=$1
count=$(grep 'result_cb request' un*/*OUT | wc -l)
now=$(date +%s)
start=$(cat un*/un*prof | grep cu_exec_start | cut -f 1 -d , | sort -n | head -n 1)
stop=$( cat un*/un*prof | grep cu_exec_stop  | cut -f 1 -d , | sort -n | tail -n 1)

test -z "$total" && total=6700000
test -z "$stop"  && stop=$now

runtime=$((stop - start))
rate=$((count / runtime))
est=$((total / count * runtime))

printf "total   : %10d\n" $total
printf "count   : %10d\n" $count
printf "rate    : %10.1f /sec\n" $(echo "$count / $runtime"           | bc -l)
printf "          %10.1f /min\n" $(echo "$count / $runtime * 60"      | bc -l)
printf "          %10.1f /hrs\n" $(echo "$count / $runtime * 60 * 60" | bc -l)
printf "runtime : %10d sec\n"    $(echo "$runtime"                    | bc -l)
printf "          %10.1f min\n"  $(echo "$runtime / 60"               | bc -l)
printf "          %10.1f hrs\n"  $(echo "$runtime / 60 / 60"          | bc -l)
printf "estimate: %10d sec\n"    $(echo "$est"                        | bc -l)
printf "          %10.1f min\n"  $(echo "$est     / 60"               | bc -l)
printf "          %10.1f hrs\n"  $(echo "$est     / 60 / 60"          | bc -l)


