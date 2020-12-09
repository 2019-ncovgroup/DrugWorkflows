#!/bin/bash
#
# Convert a SMILES string to a MOL2 file in a way that is compatible
# with GNU Parallel.
#
# This script takes 1 argument that contains the SMILES string
# followed by the identifier. This is essentially 1 line of
# ligand library.
#
declare -a fields
if [ ${#0} -gt 17 ]
then
  # this command was called with an explicit path
  path=`readlink -f $0`
  path=`dirname $path`
else
  # this command is in the PATH
  path=`which smiles_to_mol2.sh`
  path=`dirname $path`
fi
fields=($1)
smiles=${fields[0]}
id=${fields[1]}
$path/echo_smiles.py "$smiles" | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2 > $id.mol2
