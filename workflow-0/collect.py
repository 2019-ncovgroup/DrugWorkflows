#!/usr/bin/env python3

import os
import sys
import glob

data = dict()
sids = sys.argv[1:]

print()
for sid in sids:
  # print(sid)
    oeb = None
    smi = None
    for task in sorted(glob.glob('%s/pilot.*/unit.*/unit.*.sh' % sid)):
        uid = os.path.basename(task)[:-3]
        with open(task, 'r') as fin:
            for line in fin.readlines():
                idx1 = line.find('theta_dock')
                idx2 = line.find('>')
                if idx1 < 0: continue
                if idx2 < 0: idx2 = len(line)
                try:
                    _, _, smi, oeb, _, idx_start, idx_count = line[idx1:idx2].split()
                except:
                    print(line[idx:idx2])
                    raise
                break
        if not oeb:
          # print('skip %s' % task)
            continue
        oeb       = oeb.strip('"')
        smi       = smi.strip('"')
        idx_start = idx_start.strip('"')
        idx_count = idx_count.strip('"')
        oeb       = os.path.basename(oeb)
        smi       = os.path.basename(smi)
        idx_start = int(idx_start)
        idx_count = int(idx_count)

        if oeb not in data:
            data[oeb] = set()

        cnt = 0
        with open('%s/STDOUT' % os.path.dirname(task), 'r') as fin:
            for line in fin.readlines():
                if 'test,pl_pro' not in line:
                    continue
                data[oeb].add(line)
                cnt += 1
      # print('    ', uid, oeb, smi, idx_start, idx_count, cnt)
    if not oeb:
        print(sid)
    else:
        print(sid, oeb, len(data[oeb]))
print()

for oeb in data:
    fname = '%s.out' % oeb[:-4]
    print('write %s' % fname)
    if os.path.exists(fname):
        print('WARNING: %s exists - appending data' % fname)
    with open(fname, 'a') as fout:
        for line in sorted(list(data[oeb])):
            if 'SMILES invalid' not in line:
                fout.write(line)
print()

