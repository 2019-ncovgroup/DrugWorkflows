import os 
import subprocess
# import tempfile 
import MDAnalysis as mda 

from .utils import add_hydrogen, remove_hydrogen 
from .utils import get_ligand, get_protein
from .utils import run_at_temp, to_pdb


@run_at_temp
def ParameterizeAMBER_comp(pdb_lig, pdb_pro, add_sol=True):
    """
    Copied from InspireMD
    This function is pretty much a wrapper for antechamber & tleap. 
    Only suitable for single protein and single ligand 
    """   
    output_path = os.path.abspath(os.path.dirname(pdb_lig))
    output_top = os.path.join(output_path, 'comp.prmtop')
    output_inpcrd = os.path.join(output_path, 'comp.inpcrd')
    output_pdb = os.path.join(output_path, 'comp.pdb')

    remove_hydrogen(pdb_pro, pdb_pro)
    pdb_lig = add_hydrogen(pdb_lig)
    subprocess.check_output(f'antechamber -i {pdb_lig} -fi pdb -o lig.mol2 -fo mol2 -c bcc -pf y -an y', shell=True)
    subprocess.check_output(f'parmchk2 -i lig.mol2 -f mol2 -o lig.frcmod', shell=True)
    with open(f'leap.in', 'w+') as leap:
        leap.write("source leaprc.protein.ff14SBonlysc\n")
        leap.write("source leaprc.gaff\n")
        leap.write("source leaprc.water.tip3p\n")
        leap.write("set default PBRadii mbondi3\n")
        leap.write(f"rec = loadPDB {pdb_pro} # May need full filepath?\n")
        # leap.write("saveAmberParm rec apo.prmtop apo.inpcrd\n")
        leap.write("lig = loadmol2 lig.mol2\n")
        leap.write("loadAmberParams lig.frcmod\n")
        # leap.write("saveAmberParm lig lig.prmtop lig.inpcrd\n")
        leap.write("comp = combine {rec lig}\n")
        if add_sol: 
            leap.write("solvatebox comp TIP3PBOX 15\n")
            leap.write("addions comp Na+ 0\n")
            leap.write("addions comp Cl- 0\n")        
        leap.write(f"saveAmberParm comp {output_top} {output_inpcrd}\n")
        leap.write(f"savepdb comp {output_pdb}\n")
        leap.write("quit\n")
    subprocess.check_output(f'tleap -f leap.in', shell=True)
    if os.path.exists(output_top) and os.path.exists(output_inpcrd): 
        # to_pdb(output_inpcrd, output_top, output_pdb)
        comp_info =  {'top_file': output_top, 
                      'inpcrd_file': output_inpcrd, 
                      'pdb_file': output_pdb}
        return comp_info
    else: 
        raise Exception("Leap failed to build topology, check errors...")


# @run_at_temp
def ParameterizeAMBER_comp2(pdb_comp, add_sol=True): 
    """
    This function is to build complex system with multiple chains and 
    ligands 
    """
    # protein operations 
    pdb_pro = get_protein(pdb_comp)
    # ligand operations 
    pdb_lig = get_ligand(pdb_comp)
    params = ParameterizeAMBER_comp(pdb_lig, pdb_pro)
    return params


@run_at_temp
def ParameterizeAMBER_prot(pdb_pro, add_sol=True):
    """
    This functions is to parameterize a single protein
    """
    output_path = os.path.abspath(os.path.dirname(pdb_pro))
    output_top = os.path.join(output_path, 'prot.prmtop')
    output_inpcrd = os.path.join(output_path, 'prot.inpcrd')
    output_pdb = os.path.join(output_path, 'prot.pdb')
    with open('leap.in', 'w') as leap: 
        leap.write("source leaprc.protein.ff14SBonlysc\n")
        leap.write("source leaprc.gaff\n")
        leap.write("source leaprc.water.tip3p\n")
        leap.write("set default PBRadii mbondi3\n")
        leap.write(f"prot = loadPDB {pdb_pro} # May need full filepath?\n")
        if add_sol:
            leap.write("solvatebox prot TIP3PBOX 15\n")
            leap.write("addions prot Na+ 0\n")
            leap.write("addions prot Cl- 0\n")
        leap.write(f"saveAmberParm prot  {output_top} {output_inpcrd}\n")
        leap.write(f"savepdb prot {output_pdb}\n")
        leap.write("quit\n")
    subprocess.check_output(f'tleap -f leap.in', shell=True)
    if os.path.exists(output_top) and os.path.exists(output_inpcrd): 
        # to_pdb(output_inpcrd, output_top, output_pdb)
        prot_info =  {'top_file': output_top, 
                      'inpcrd_file': output_inpcrd, 
                      'pdb_file': output_pdb}
        return prot_info
    else: 
        raise Exception("Leap failed to build topology, check errors...")


@run_at_temp
def ParameterizeAMBER_lig(pdb_lig, add_sol=True):
    """
    Copied from InspireMD
    This function is pretty much a wrapper for antechamber & tleap. 
    """   
    output_path = os.path.abspath(os.path.dirname(pdb_lig))
    output_top = os.path.join(output_path, 'lig.prmtop')
    output_inpcrd = os.path.join(output_path, 'lig.inpcrd')
    output_pdb = os.path.join(output_path, 'lig.pdb')

    pdb_lig = add_hydrogen(pdb_lig)
    subprocess.check_output(f'antechamber -i {pdb_lig} -fi pdb -o lig.mol2 -fo mol2 -c bcc -pf y -an y', shell=True)
    subprocess.check_output(f'parmchk2 -i lig.mol2 -f mol2 -o lig.frcmod', shell=True)
    with open(f'leap.in', 'w+') as leap:
        leap.write("source leaprc.protein.ff14SBonlysc\n")
        leap.write("source leaprc.gaff\n")
        leap.write("source leaprc.water.tip3p\n")
        leap.write("set default PBRadii mbondi3\n")
        leap.write("lig = loadmol2 lig.mol2\n")
        leap.write("loadAmberParams lig.frcmod\n")
        if add_sol: 
            leap.write("solvatebox lig TIP3PBOX 15\n")
            leap.write("addions lig Na+ 0\n")
            leap.write("addions lig Cl- 0\n")
        leap.write(f"saveAmberParm lig  {output_top} {output_inpcrd}\n")
        leap.write(f"savepdb lig {output_pdb}\n")
        leap.write("quit\n")
    subprocess.check_output(f'tleap -f leap.in', shell=True)

    if os.path.exists(output_top) and os.path.exists(output_inpcrd): 
        # to_pdb(output_inpcrd, output_top, output_pdb)
        lig_info =  {'top_file': output_top, 
                     'inpcrd_file': output_inpcrd, 
                     'pdb_file': output_pdb}
        return lig_info
    else: 
        raise Exception("Leap failed to build topology, check errors...")
