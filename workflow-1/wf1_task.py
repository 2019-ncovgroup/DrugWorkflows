#!/usr/bin/env python3

import os
import sys

import numpy as np

from impress_md import interface_functions


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':
    print('==== start')

    work = sys.argv[1]
    mode = sys.argv[2]
    rank = sys.argv[3]

    print('==== work: [%s]' % work)
    print('==== mode: [%s]' % mode)
    print('==== rank: [%s]' % rank)

    name = os.path.basename(rank)
    print('==== ', mode, name)

    if mode == 'minimize':
        try:
            # O(100k)
            print('=== run  Minimize  %s' % name)
            val = interface_functions.RunMinimization_(
                                 rank, rank, write=True, gpu=True)
            print('=== run  Minimized %s: %s' % (name, val))

            with open('%s/work_stats/%s.stat' % (work, name), 'a') as fout:
                fout.write('energy: %s\n' % val)

            if val == np.nan or val >= 0:
                print('=== skip MMGBSA    %s [val=%s]' % (name, val))
                sys.exit(1)
            else:
                print('=== run  MMGBSA    %s [val=%s]' % (name, val))
                sys.exit(0)

        except Exception as e:
            print('=== skip MMGBSA    %s [err=%s]' % (name, e))
            sys.exit(2)

    elif mode == 'mmgbsa':

        try:
            # O(10k)
            interface_functions.RunMMGBSA_(rank, rank, gpu=True, niters=5000)

        except Exception as e:
            print('=== fail MMGBSA    %s [err=%s]' % (name, e))


    else:
        assert(False), '--%s--' % mode


# ------------------------------------------------------------------------------
