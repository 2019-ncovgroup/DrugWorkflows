#!/usr/bin/env python3

import glob

import numpy as np

from impress_md import interface_functions


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    dbase_name   = 'adpr_ena_db'
    target_name  = 'pl_pro'

    for ligand_name in sorted(glob.glob('%s/rank*' % dbase_name)):

        mmgbsa = True
        try:
            # O(100k)
            print('=== run  Minimize  %s' % ligand_name)
            val = interface_functions.RunMinimization_(
                                 ligand_name, ligand_name, write=True, gpu=True)

            if val == np.nan or val >= 0:
                print('=== skip MMGBSA    %s [val=%s]' % (ligand_name, val))
                mmgbsa = False
            else:
                print('=== run  MMGBSA    %s [val=%s]' % (ligand_name, val))

        except Exception as e:
            print('=== skip MMGBSA    %s [err=%s]' % (ligand_name, e))
            mmgbsa = False

        if  not mmgbsa:
            continue

        try:
            # O(10k)
            interface_functions.RunMMGBSA_(ligand_name, ligand_name, gpu=True)
        except Exception as e:
            print('=== fail MMGBSA    %s [err=%s]' % (ligand_name, e))
            mmgbsa = False

# ------------------------------------------------------------------------------
