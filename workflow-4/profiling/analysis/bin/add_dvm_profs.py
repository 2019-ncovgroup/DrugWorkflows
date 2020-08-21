#!/usr/bin/env python

import os
import re
import sys
import datetime

import radical.utils as ru

sid  = sys.argv[1]
log  = sys.argv[2]
loc  = sys.argv[3]

event_map = {
        'Starting ORTE DVM'          : {ru.EVENT : 'orte_dvm_start',
                                        ru.UID   : 'pilot.0000'},
        'ORTE DVM startup successful': {ru.EVENT : 'orte_dvm_ok',
                                        ru.UID   : 'pilot.0000'}
        }

t_format = '%Y-%m-%d %H:%M:%S,%f'
t_offset = datetime.timedelta(hours=4)
t_zero   = datetime.datetime(1970,1,1) - t_offset

regexes  = list()
for check in event_map:
    regexes.append([check, re.compile (check)])

if not log.endswith('.log'):
    raise ValueError('%s is not a logfile' % log)

blog = os.path.basename(log)
prof = '%s/pilot.0000/%s.prof' % (loc, blog[:-4])

if not os.path.isfile(log):
    print '- %s' % log
    sys.exit(1)
  # raise ValueError('logfile not found: %s' % log)

if not os.path.isfile(prof):
    print '- %s' % prof
    sys.exit(1)
  # raise ValueError('profile not found: %s' % prof)

with open (prof, 'a') as f_prof, \
     open (log , 'r') as f_log   :

    for line in f_log.readlines():
        try:
            elems  = line.split(':')
            msg    = elems[7].strip()
            tstamp = ':'.join(elems[0:3])
        except:
            continue

      # print msg
        for check,regex in regexes:
            if check in msg:
                then = datetime.datetime.strptime(tstamp, t_format)
                sse  = (then - t_zero).total_seconds()
              # print 'match: %s --> %.2f' % (tstamp, sse/60)
                stub = event_map[check]
                out  = ru.Profiler.format(timestamp=sse,
                                          event    = stub.get(ru.EVENT, ''),
                                          comp     = stub.get(ru.COMP,  ''),
                                          tid      = stub.get(ru.TID,   ''),
                                          uid      = stub.get(ru.UID,   ''),
                                          state    = stub.get(ru.STATE, ''),
                                          msg      = stub.get(ru.MSG,   ''))
              # print out
                f_prof.write('%s\n' % out)

print '= %s' % sid




