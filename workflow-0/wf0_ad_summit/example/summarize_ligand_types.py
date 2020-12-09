#!/usr/bin/env python
'''
Report the list of all atoms types in the ligand dictionary file.

The ligand dictionary file contain inform in this format:

summary = d = {}
d['MHAKUSQMTWYHGM-UHFFFAOYSA-N'] = {'atom_types': ['A', 'C', 'F', 'N', 'NA', 'OA', 'S' ],
                        'rbonds':5,
                        'zero_charge' : [],
                        }
d['PWKZDEFKCSDFFT-UHFFFAOYSA-N'] = {'atom_types': ['A', 'C', 'N', 'OA' ],
                        'rbonds':7,
                        'zero_charge' : [],
                        }

This script collects a list of all unique atoms types in the dictionary
and prints that.
'''
import sys


def parse_arguments():
    '''
    Parse the command line arguments.

    The only command line argument for this script is the name of the
    ligand dictionary file.
    '''
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("LigandDict",help="Filename for the ligand dictionary file")
    args=parser.parse_args()
    return args

def extract_atom_types(d):
    '''
    Extract a list of unique atom types from the summary dictionary.

    The dictionary "d" is a dictionary of dictionaries. The top
    level dictionary has an entry for each ligand. Each entry
    is another dictionary that contains an entry "atom_types"
    that is a list of all atom types in that ligand. We need
    a list of all unique atom types across all ligands.

    This function returns that list.
    '''
    all_atom_types = []
    for ligand in d.items():
        ligand_id, ligand_data = ligand
        ligand_atom_types = ligand_data["atom_types"]
        all_atom_types.extend(x for x in ligand_atom_types if x not in all_atom_types)
    return all_atom_types
        
    

if __name__ == "__main__":
    args=parse_arguments()
    ligand_dict=str(args.LigandDict)
    exec(open(ligand_dict).read())
    atom_types=extract_atom_types(d)
    length=len(atom_types)
    ii=0
    sys.stdout.write(atom_types[ii])
    ii+=1
    while (ii < length):
        sys.stdout.write(","+atom_types[ii])
        ii+=1
