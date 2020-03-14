#!/usr/bin/env python3

GAP = 10

import os
import sys
import radical.utils as ru

out = sys.argv[1].strip()
inp = sys.argv[2].strip()

smi = os.path.basename(inp)[:-4]
oeb = os.path.basename(out)[:-4]

num = int(ru.sh_callout('wc -l %s' % inp)[0].split()[0])

rec = set()
dup = list()
with open(out, 'r') as fin:
    try:
        for line in fin.readlines():
            idx = int(line.split(' ', 1)[0])
            if idx in rec:
                dup.append(idx)
            rec.add(idx)
    except:
        print('failed: %s' % line)
        raise

rmin = None
rmax = None
miss = 0
gaps = list()
GAPS = list()
for i in range(num):
    if i in rec:
        if rmin:
            if rmin == i - 1:
                GAPS.append('%23d' % i)
                if 1 >= GAP:
                    gaps.append('%23d' % i)
                rmin = None
                rmax = None
            elif rmax:
                gap = rmax - rmin + 1
                GAPS.append('%10d - %10d' % (rmin, rmax)) 
                if gap >= GAP:
                    gaps.append('%10d - %10d [%10d]'
                               % (rmin, rmax, rmax - rmin + 1))
                rmax = None
                rmin = None
            else:
                assert(0), [rmin, rmax, i]
    else:
        miss += 1
        if not rmin:
            rmin = i
        rmax = i
    if not num % 1000:
        sys.stdout.write('.')
        sys.stdout.flush()
if rmin:
    gaps.append('%10d - %10d [%10d]'
               % (rmin, num, num - rmin + 1))

with open('%s.stat' % oeb, 'w') as fout:
    fout.write('\n')
    fout.write('receptor  : %-30s  [%10d]\n' % (oeb, len(rec)))
    fout.write('smiles    : %-30s  [%10d]\n' % (smi, num))
    fout.write('missing   : %30.1f%% [%10d]\n' % (100.0 * miss / num, miss))
    first = True
    for gap in gaps:
        if first: fout.write('gaps >= %2d:         %s\n' % (GAP, gap))
        else    : fout.write('          :         %s\n'  %       gap )
        first = False

with open('%s.gaps' % oeb, 'w') as fout:
    for gap in GAPS:
        fout.write('%s\n' % gap)

os.system('cat %s.stat' % oeb)

