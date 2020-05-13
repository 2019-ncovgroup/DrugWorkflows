import os 
import glob 
# import json 
import shutil
import MDAnalysis as mda 

from comp_sim.utils import only_protein, align_to_template
from comp_sim.param import ParameterizeAMBER_comp2
from comp_sim.param import ParameterizeAMBER_prot 

host_dir = os.getcwd() 
pdb_files = sorted(glob.glob(host_dir + '/pdb/*.pdb') )

prot_files = [pdb for pdb in pdb_files if only_protein(pdb)] 

ref_pdb = prot_files[0]
info_list = []
for pdb in pdb_files: 
    pdb_code = os.path.basename(pdb)[:-4] 
    work_dir = os.path.join(host_dir, 'input_' + pdb_code) 
    os.makedirs(work_dir, exist_ok=True) 
    pdb_copy = os.path.join(work_dir, os.path.basename(pdb))
    # align all targets to template 
    align_to_template(pdb, ref_pdb, pdb_copy)
    # shutil.copy2(pdb, pdb_copy)
    os.chdir(work_dir) 
    if only_protein(pdb): 
        info = ParameterizeAMBER_prot(pdb_copy)
    else: 
        info = ParameterizeAMBER_comp2(pdb_copy) 
    print(info) 
    info_list.append(info)
    os.chdir(host_dir) 

# input_filepath = os.path.abspath('./input_conf.json') 
# with open(input_filepath, 'w') as input_file: 
#     json.dump(info_list, input_file)
