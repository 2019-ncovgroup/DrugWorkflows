#!/bin/sh

watch -n 60 "~/wf0_stats.sh ; echo; squeue -u rpilot -o '%.18i %.9P %.10j %.8u %.2t %.10M %.6D %R' | cut -c 1-150 | sort -n"
