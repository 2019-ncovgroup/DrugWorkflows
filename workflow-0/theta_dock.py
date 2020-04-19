#!/usr/bin/env python3

import os
import sys
import re
import pandas as pd

from impress_md import interface_functions


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    assert('OE_LICENSE' in os.environ)

    smiles_files = pd.read_csv(sys.argv[1], sep=' ', header=None)
    target_filoe = sys.argv[2]
    start_idx    = int(sys.argv[3])
    n_smiles     = int(sys.argv[4])
    has_ligand   = bool(sys.argv[5])
    
    force_flipper = True
    high_resolution = True
    
    pdb_name = re.sub("_receptor.oeb", "", target_filoe).split("/")[-1]
    
    
    docker, receptor = interface_functions.get_receptr(target_filoe, has_ligand=has_ligand, high_resolution=high_resolution)

    for pos in range(start_idx, start_idx + n_smiles):

        smiles      = smiles_files.iloc[pos, 0]
        ligand_name = smiles_files.iloc[pos, 1]
        _, res = interface_functions.RunDocking_(smiles,
                                                dock_obj=docker,
                                                pos=pos,
                                                name=ligand_name,
                                                target_name=pdb_name,
                                                force_flipper=force_flipper)
        print(pos, res, end='')


# ------------------------------------------------------------------------------

