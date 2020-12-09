# Autodock-GPU related scripts

Autodock-GPU works a bit different from Autodock 4.2. As a 
result the scripts needed to run docking screen with it
have to be adapted a bit. The main difference is that
Autodock-GPU seems to want to work on a batch of ligands
rather than dock an individual ligand. This design alternative
has some knock on effects:

- The ligand SMILES strings need to be converted to PDBQT files ahead of time
- The docking grids need to be set up for all atom types across all ligands
- A file listing all ligands needs to be passed to Autodock-GPU

This directory contains scripts that have been adapted to 
accommodate these differences.

There are following scripts:

- **smiles\_dock\_gpu.sh**: A variant of the smiles\_dock.sh script adapted to be
  used with Autodock-GPU. It is designed to dock the ligands in a given sub-set
  of all ligands. 
  - This script takes 4 or 5 positional arguments
    - 1. The filename for the protein structure in PDBQT format (but without extension).
         For example: 3CLPro_protein. The PDBQT files has to be generated from the PDB file
         of the protein using the command: `pythonsh $AUTODOCKTOOLS_UTIL/prepare_receptor4.py -A checkhydrogens -r $1.pdb -o $1.pdbqt`. Note that the PDBQT file has to be generated
         only once for a given protein. It can be reused for all sub-sets of ligands. For
         that reason the PDBQT file is generated outside of this script.
    - 2. The filename containing a ligand sub-set. The ligand sub-set is given by lines
         each holding a SMILES string for the ligand and a ligand identifier. For example:
         ```
         C12C3C4C1(C5C2C3(C(C45)(O)O)Br)C(=O)[O-] ORD-MCULE-9093963410_1
         C12C3C4C5C3(C1C5C4(C2O)Br)Br ORD-MCULE-9924047831_1
         c12c(c(c(c(c1Br)N(=O)=O)Br)N(=O)=O)nn[nH]2 ORD-MCULE-8943695820_1
         c12c(c(c(c(c1Cl)Cl)Cl)Cl)C(=O)N(C2=O)N ORD-MCULE-5924799362_1
         c12c(c(c(c(c1Cl)Cl)Cl)Cl)C(=O)NC2=O ORD-MCULE-8136162164_1
         ```
         I.e. the SMILES string and the identifier are space separated.
    - 3. The pocket center position given as "xcoord,ycoord,zcoord". 
         For example: `"-10.520,-2.322,-20.631"`.
    - 4. The number of grid points given as "nptsx,nptsy,nptsz", where 
         nptsx, nptsy, and nptsz have to be even numbers. For example:
         `"54,52,60"`.
    - 5. Flexible residues [optional and currently not used in any of our calculations].
- **smiles_to_mol2.sh**: A script that runs OpenBabel to convert a SMILES string
  into a MOL2 file in such a way that the script can be invoked from GNU Parallel
  to speed up the structure files generation.
- **summarize_ligand_types.py**: The AutodockTools prepare_ligand4.py script can 
  provide summary information for each ligand. However, we need to know all
  atom types across all ligands. For some reason AutodockTools does not have
  a script to extract that information. This script does that little (but
  crucial) step.

Dependencies:

- GNU Parallel: https://www.gnu.org/software/parallel/
  - This is a shell script to execute jobs in parallel.
  - A job can be a script to be execute for each line in the input.
  - See the webpage for more details. 
- echo_smiles.py: a script that checks whether the SMILES string contains a ligand
  consisting of multiple fragments. This script is kept one directory up from this
  location. In most cases this could be replaced with regular Unix `echo`.
- Python
