#!/bin/sh

watch -n 300 "~/wf0_stats.sh ; echo; squeue -u rpilot -o '%.18i %.9P %.10j %.8u %.2t %20S %.10M %.6D %R' | cut -c 1-150 | sort -n; printf '%52s' ' '; date +'%Y-%m-%dT%H:%M:%S'"
