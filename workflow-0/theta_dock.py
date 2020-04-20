#!/usr/bin/env python3

import os
import re
import sys
import pandas as pd
import numpy as np
from openeye import oechem
from impress_md import interface_functions

def get_root_protein_name(file_name):
   return file_name.split("/")[-1].split(".")[0]

def get_smiles_col(col_names):
    return int(np.where(['smile' in s.lower() for s in col_names])[0][0])

def get_ligand_name_col(col_names):
    return int(np.where(['id' in s.lower() or 'title' in s.lower() or "name" in s.lower() for s in col_names])[0][0])



# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    assert('OE_LICENSE' in os.environ)
    input_smiles_file = sys.argv[1]
    target_file = sys.argv[2]
    start_idx    = int(sys.argv[3])
    n_smiles     = int(sys.argv[4])
    output_poses = True
    
   
    ## setting don't change
    use_hybrid = True
    force_flipper = True
    high_resolution = True

    #set logging if used
    if output_poses:
        ofs = oechem.oemolostream()
        ofs.SetFormat(oechem.OEFormat_SDF)
    else:
        ofs = None

    # get root receptor Name
    pdb_name = get_root_protein_name(target_file)

    smiles_file = pd.read_csv(input_smiles_file)
    columns = smiles_file.columns.tolist()
    smiles_col = get_smiles_col(columns)
    name_col = get_ligand_name_col(columns)

    docker, receptor = interface_functions.get_receptor(target_file, use_hybrid=use_hybrid, high_resolution=high_resolution)

#    for pos in range(start_idx, start_idx + n_smiles):
#
#        smiles      = smiles_files.iloc[pos, 0]
#        ligand_name = smiles_files.iloc[pos, 1]
#        score, res  = interface_functions.RunDocking_(
#                smiles, None, None, dbase_name, target_name,
#                pos=pos, write=True, receptor_file=None,
#                name=ligand_name, docking_only=True,
#                dock_obj=docker, recept=receptor)
#        print(pos, res, end='')

#    pdb_name = re.sub("_receptor.oeb", "", target_filoe)
    
    for pos in range(start_idx, start_idx + n_smiles):
#        smiles      = smiles_files.iloc[pos, 0]
#        ligand_name = smiles_files.iloc[pos, 1]
#        score, res  = interface_functions.RunDocking_(
#            smiles, docker, pos=pos, name=ligand_name, target_name=pdb_name)
#        print(pos, res, end='')
        smiles = smiles_file.iloc[pos, smiles_col]
        ligand_name = smiles_file.iloc[pos, name_col]
        score, res, ligand = interface_functions.RunDocking_(smiles,
                                                dock_obj=docker,
                                                pos=pos,
                                                name=ligand_name,
                                                target_name=pdb_name,
                                                force_flipper=force_flipper)
        
        #print(res, end='')
        if ofs and ligand is not None:
            for i, col in enumerate(columns):
                value = str(smiles_file.iloc[pos, i]).strip()
                if col.lower() != 'smiles' and 'na' not in value.lower() and len(value) > 1:
                    try:
                        oechem.OESetSDData(ligand, col, value)
                    except ValueError:
                        pass
            oechem.OEWriteMolecule(ofs, ligand)

    if ofs is not None:
        ofs.close()

# ------------------------------------------------------------------------------

