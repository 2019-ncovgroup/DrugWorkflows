#!/bin/sh

# ------------------------------------------------------------------------------
# cleanup traces from previous runs
#
rm -rf /tmp/sbox_* /tmp/*.lck /tmp/tools/


# ------------------------------------------------------------------------------
#
# unpack autotools
#
tar  -C "/tmp/" -xf "$RP_UNIT_SANDBOX/wf0_ad_prep.tar"
echo "HOSTNAME: $(hostname -f) $(ls -l /tmp/tools/bin/pythonsh)"



# # ------------------------------------------------------------------------------
# #
# # create task sandboxes (one per core)
# #
# cpn=$(cat /proc/cpuinfo | grep -e '^processor\s*:' | wc -l)
# i=0
# while test "$i" -lt "$cpn"
# do
#     mkdir "/tmp/sbox_$i"
#     i=$((i+1))
# done


# ------------------------------------------------------------------------------

