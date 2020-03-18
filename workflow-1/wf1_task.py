#!/usr/bin/env python3

import os
import glob

import numpy as np

from impress_md import interface_functions


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    dbase_loc    = '/gpfs/alpine/med110/scratch/merzky1/covid/DrugWorkflows/workflow-1/data/'
    dbase_name   = 'adpr_ena_db'
    dbase_path   = '%s/%s' % (dbase_loc, dbase_name)
    target_name  = 'pl_pro'

    ligands = sorted(list(glob.glob('%s/rank*' % dbase_path)))
    print('ligands: %d' % len(ligands))

    ligands = ligands[:2]

    for ligand in ligands:

        name = os.path.basename(ligand)
        print(name)

        mmgbsa = True
        try:
            # O(100k)
            print('=== run  Minimize  %s' % name)
            val = interface_functions.RunMinimization_(
                                 ligand, ligand, write=True, gpu=True)

            if val == np.nan or val >= 0:
                print('=== skip MMGBSA    %s [val=%s]' % (name, val))
                mmgbsa = False
            else:
                print('=== run  MMGBSA    %s [val=%s]' % (name, val))

        except Exception as e:
            print('=== skip MMGBSA    %s [err=%s]' % (name, e))
            mmgbsa = False

        if  not mmgbsa:
            continue

        try:
            # O(10k)
            interface_functions.RunMMGBSA_(ligand, ligand, gpu=True)
        except Exception as e:
            print('=== fail MMGBSA    %s [err=%s]' % (name, e))
            mmgbsa = False


# ------------------------------------------------------------------------------
