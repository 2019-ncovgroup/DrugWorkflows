import os 
import h5py 
import tempfile 
import subprocess
import numpy as np 
import MDAnalysis as mda 
import parmed as pmd 

import simtk.openmm.app as app
import simtk.openmm as omm
import simtk.unit as u 

from MDAnalysis.analysis import distances
from MDAnalysis.analysis import align


# def pdb_split(pdb_file): 
#     """
#     This function is to split a complex pdb into a list of pdbs for each 
#     components (chains and ligands) 
#     """
#     mda_trj = mda.Universe(pdb_file) 
#     pdb_name = os.path.basename(pdb_file).replace('.pdb', '')
#     pdb_dir = os.path.dirname(pdb_file)

#     # get all protein chains 
#     prot_list = []
#     protein = mda_trj.select_atoms('protein')
#     for seg in protein.segments: 
#         seg_pdb_file = os.path.join(pdb_dir, f"{pdb_name}_{seg.segid}.pdb") 
#         seg.atoms.write(seg_pdb_file) 
#         prot_list.append(seg_pdb_file) 

#     lig_list = [] 
#     mda_ligs = mda_trj.select_atoms('not protein') 
#     for i, frag in enumerate(mda_ligs.fragments): 
#         frag_pdb_file = os.path.join(pdb_dir, f"{pdb_name}_{frag.id}.pdb")
#     return prot_list, lig_list


def get_ligand(pdb_file): 
    mda_trj = mda.Universe(pdb_file)
    lig = mda_trj.select_atoms('not protein') 
    pdb_lig = os.path.abspath('./lig.pdb')
    lig.write(pdb_lig)
    return pdb_lig


def get_protein(pdb_file): 
    mda_trj = mda.Universe(pdb_file)
    lig = mda_trj.select_atoms('protein') 
    pdb_lig = os.path.abspath('./prot.pdb')
    lig.write(pdb_lig)
    return pdb_lig


def only_protein(pdb_file): 
    mda_trj = mda.Universe(pdb_file)
    not_prot = mda_trj.select_atoms('not protein') 
    if not_prot.n_atoms == 0: 
        return True
    else: 
        return False 


def run_at_temp(func): 
    """
    Run functions at a temp dir
    """
    def wrapper(*args, **kwargs): 
        current_dir = os.getcwd()
        temp_path = tempfile.TemporaryDirectory() 
        os.chdir(temp_path.name) 
        func(*args, **kwargs)
        os.chdir(current_dir) 
    return wrapper


def clean_pdb(pdb_file): 
    """
    Remove all entris in pdb files other than `ATOM` and HETATM`
    """
    with open(pdb_file, 'r') as pdb: 
        pdb_atoms = [
            line for line in pdb 
            if line.startswith('ATOM') or line.startswith('HETATM')]
    with open(pdb_file, 'w') as pdb: 
        pdb.write(''.join(pdb_atoms))


def to_pdb(pos_file, top_file, pdb_file): 
    top = pmd.load_file(top_file, xyz=pos_file) 
    top.write_pdb(pdb_file)


def missing_hydrogen(pdb_file): 
    """
    Check whether a pdb file contains H atoms

    Parameters
    ----------
    pdb_file : str 
        path to input pdb file 

    Returns
    -------
    missingH : bool 
        True if missing H, false otherwise 
    """
    trj = mda.Universe(pdb_file) 
    missingH = not np.any(['H' in name for name in trj.atoms.names]) 
    return missingH


def remove_hydrogen(pdb_file, pdb_noH_file): 
    """
    remove H atoms from a pdb file 

    Parameters
    ----------
    pdb_file : str 
        path to input pdb file 
    pdb_noH_file : str 
        path to write pdb file with H removed 
    """
    trj = mda.Universe(pdb_file) 
    trj_noH = trj.select_atoms('not name H* and not name h*') 
    trj_noH.write(pdb_noH_file)


def add_hydrogen(pdb_file): 
    """
    add hydrogens to pdb structure if missing hydrogen atoms 
    obabel -ipdb adp.pdb -h -opdb >  adph.pdb
    """
    if not missing_hydrogen(pdb_file): 
        remove_hydrogen(pdb_file, pdb_file)

    pdb_h = pdb_file[:-4] + '_h.pdb'
    subprocess.check_output(
        f'obabel -ipdb {pdb_file} -h -opdb >  {pdb_h}',
        shell=True)
    clean_pdb(pdb_h)
    return pdb_h


def align_to_template(pdb_file, ref_file, pdb_output): 
    """
    align frame to target 
    """
    pdb = mda.Universe(pdb_file) 
    ref = mda.Universe(ref_file)
    _ = align.alignto(pdb, ref, select='protein and name CA')
    pdb.atoms.write(pdb_output)


class ContactMapReporter(object):
    def __init__(self, file, reportInterval):
        self._file = h5py.File(file, 'w', libver='latest')
        self._file.swmr_mode = True
        self._out = self._file.create_dataset(
            'contact_maps', shape=(2, 0), 
            maxshape=(None, None))
        self._reportInterval = reportInterval

    def __del__(self):
        self._file.close()

    def describeNextReport(self, simulation):
        steps = self._reportInterval - simulation.currentStep%self._reportInterval
        return (steps, True, False, False, False, None)

    def report(self, simulation, state):
        ca_indices = []
        for atom in simulation.topology.atoms():
            if atom.name == 'CA':
                ca_indices.append(atom.index)
        positions = np.array(state.getPositions().value_in_unit(u.angstrom))
        time = int(np.round(state.getTime().value_in_unit(u.picosecond)))
        positions_ca = positions[ca_indices].astype(np.float32)
        distance_matrix = distances.self_distance_array(positions_ca)
        contact_map = (distance_matrix < 8.0) * 1.0 
        new_shape = (len(contact_map), self._out.shape[1] + 1) 
        self._out.resize(new_shape)
        self._out[:, new_shape[1] - 1] = contact_map
        self._file.flush()
