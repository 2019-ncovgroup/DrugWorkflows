#!/usr/bin/env python3

import os
import sys
import glob


def parse_csv():

    fname    = sys.argv[1]
    iname    = '%s.idx' % fname
    header   = None
    idxs     = list()
    i        = 0

    print('csv', fname)
    print('idx', iname)

    if not os.path.isfile(iname):
        # build indexes
        print('create index %s' % iname)
        print('read start')
        with open(fname) as fin:
            header = fin.readline()
            while True:
                idxs.append(fin.tell())
                line = fin.readline()
                if not line  : break
                if not i % 1000000:
                    print('read %d' % i)
                i += 1
                if i > 10000:
                    break
        print('read stop')

        idxs.pop()   # EOF

        columns = header.strip('\n').split(',')

        smi_col = -1
        lig_col = -1

        for idx,col in enumerate(columns):
            if 'smile' in col.lower():
                smi_col = idx
                break

        for idx,col in enumerate(columns):
            if 'id'    in col.lower() or \
               'title' in col.lower() or \
               'name'  in col.lower():
                lig_col = idx
                break

        assert(smi_col >= 0), smi_col
        assert(lig_col >= 0), lig_col

        with open(iname, 'w') as fout:
            for off in idxs:
                fout.write('%d\n' % off)

    else:
        # read indexes
        print('check cached index')
        with open(iname, 'r') as fin:
            idxs = [int(line) for line in fin.readlines()]
        idxs.pop()   # EOF

        with open(fname, 'r') as fin:
            for off in idxs:
                fin.seek(off)
                line  = fin.readline()
                print('LINE [%d]: %s' % (off, line.rstrip()))


# ------------------------------------------------------------------------------
if __name__ == '__main__':

    parse_csv()


# ------------------------------------------------------------------------------
