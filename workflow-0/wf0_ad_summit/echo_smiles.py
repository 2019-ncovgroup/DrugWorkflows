#!/usr/bin/env python
'''
Mess with SMILES strings

In our set up the compounds are specified by SMILES strings.
We echo these SMILES strings to OpenBabel to convert them to
3D structures. However, the SMILES can be severely problematic,
typically when there are multiple non-bonded fragments. Examples
are (all of which are actual approved drugs):

- Cc1ccccn1.N.[Cl-].[Cl-].[Pt+2] (DB-4455)
- S1SSSSSSS1.[99Tc] (DB-7523)
- ClCC1CO1.NCC=C (DB-546)
- Nc1ccc2c(c1)[n+](C)c1c(c2)ccc(c1)N.[Cl-] (DB-9274)
- N[C@H](C(=O)O)CS.[O-]C(=O)[C@H](C[S-])N.NCC(=O)O.[Fe+2] (DB-7645)
- OC(=O)CCc1ccc(c(c1)/N=C/c1ccccc1[O-])/N=C/c1ccccc1[O-].[Fe+4] (DB-4391)

Looking at these examples there different categories of compounds that
are relevant to the task in hand.

Some case are simple, such as DB-9274,
which is an organic ion with a trivial Chlorine ion as a counter ion. 
One can safely assume that the Chlorine is irrelevant for the 
therapeutic effect. Hence we can throw that ion away leaving us with a 
fully connected fragment. 

The other cases are much more complicated. Is DB-546 an active complex
or is one of the 2 fragments an unimportant ion? DB-4455, DB-7523, and
DB-4391 are almost certainly complexes where the metal ion has to be
in a very specific location, but this position is not encoded in the
SMILES string. DB-7645 is even worse with multiple organic fragments and
a metal ion. Clearly the metal ion has to be complexed somewhere and
at the same time non of the organic fragments look like trivial ions. 

To deal with this mess we take a simple approach:

1. Split the SMILES string at "."
2. Delete all trivial ions (K, Na, Cl, K+, Na+, Cl-, OH-, etc.)
3. If only 1 fragment remains echo it to standard output, else the situation is too complicated and we abort.
'''

def parse_arguments():
    '''
    Parse the command line arguments.

    This is mainly a SMILES string.
    '''
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("SMILES",help="SMILES string for a compound")
    args=parser.parse_args()
    return args

def is_trivial_ion(ion):
    '''
    Given an ion return if this is a trivial ion

    The input a SMILES string of an ion. Check whether this string
    matches any one of a set of known trivial ions.

    Return True if it matches any of the trivial ions.
    '''
    trivial_ions = [
       "Cl",
       "O",
       "[Na+]",
       "[K+]",
       "[Cl-]",
       "[Br-]",
       "[OH-]"
    ]
    return (ion in trivial_ions)

def reduce_ion_list(listin):
    '''
    Strip all trivial ions from the input list
    '''
    listout = []
    for ion in listin:
        if not is_trivial_ion(ion):
            listout.append(ion)
    return listout

if __name__ == "__main__":
    args=parse_arguments()
    fragment_list_in=str(args.SMILES).split(".")
    fragment_list_out=reduce_ion_list(fragment_list_in)
    if len(fragment_list_out) == 0:
        exit("Empty SMILES string remaining after deleting trivial ions")
    elif len(fragment_list_out) > 1:
        exit("SMILES string contains multiple non-bonded fragments")
    else:
        print(fragment_list_out[0])
