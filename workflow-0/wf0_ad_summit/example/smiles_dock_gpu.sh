#!/bin/bash
#
# This script takes 5 argument:
#
# - $1 the protein (in pdbqt format)
# - $2 the filename containing the SMILES string and the identifier lines
# - $3 the pocket center given as "xcoord,ycoord,zcoord"
# - $4 the number grid points given as "nptsx,nptsy,nptsz"
# - $5 the flexible residues (in pdb format) [optional]
#
#. /software/anaconda3/etc/profile.d/conda.sh
#conda activate py3
#
# Conversion of SMILES string to MOL2:
#
# - Done one at a time as OpenBabel might crash attempting this
#   and if that happens only 1 molecule is lost this way
#
#DEBUG
#env | sort
#exit
#DEBUG
if [ ${#0} -gt 14 ]
then
  # this command was called with an explicit path
  path=`readlink -f $0`
  path=`dirname $path`
else
  # this command is in the PATH
  path=`which smiles_dock.sh`
  path=`dirname $path`
fi

SCRATCH_DIR=$(mktemp -d -p ${DATADIR}) && cd $SCRATCH_DIR
declare -a fields
#NODE_SET_base=`basename ${NODE_SET}`
NODE_SET=$2
CPUS_ON_NODE=28
echo "./$1.maps.fld" > batch_file.txt


echo -n "=== prepare ligands ================"; date
parallel -a $NODE_SET --timeout=1200 -j ${CPUS_ON_NODE} "smiles_to_mol2.sh {1}"
while IFS= read -r line
do
  fields=($line)
  smiles=${fields[0]}
  id=${fields[1]}
  #$path/echo_smiles.py "$smiles" | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2 > $id.mol2
  pythonsh $AUTODOCKTOOLS_UTIL/prepare_ligand4.py -l $id.mol2 -F -o $id.pdbqt -d ./ligand_dict.py
  echo "./$id.pdbqt" >> batch_file.txt
  echo "$id"         >> batch_file.txt
done < $2


echo -n "=== prepare grids =================="; date
lig_types=`summarize_ligand_types.py ./ligand_dict.py`
cp ../$1.pdbqt .
pythonsh $AUTODOCKTOOLS_UTIL/prepare_gpf4.py  -r $1.pdbqt -p ligand_types="$lig_types" -p npts="$4" -p gridcenter="$3" -o $1.gpf
autogrid4 -p $1.gpf -l $1.glg

echo -n "=== run autodock-gpu ==============="; date
autodock_gpu_64wi -filelist ./batch_file.txt -devnum 1 -lsmet "ad"


echo -n "=== transform results =============="; date
mkdir ../results 
while IFS= read -r line
do
  fields=($line)
  smiles=${fields[0]}
  id=${fields[1]}
  pythonsh $AUTODOCKTOOLS_UTIL/write_lowest_energy_ligand.py -f $id.dlg -o ${id}_tmp.pdbqt
  obabel -ipdbqt ${id}_tmp.pdbqt -osdf | head --lines=-1 > $id.sdf
  if [ -s $id.sdf ] 
  then
    ad_score=`grep "USER    Estimated Free Energy of Binding    =" $id.dlg | grep -v "DOCKED: USER" | head --lines=1 | awk '{print $8}'`
    echo ">  <AutodockScore>" >> $id.sdf
    echo $ad_score            >> $id.sdf
    echo                      >> $id.sdf
    echo ">  <TITLE>"         >> $id.sdf
    echo $id                  >> $id.sdf
    echo                      >> $id.sdf
    echo "\$\$\$\$"           >> $id.sdf
    mv $id.sdf ../results
  fi
done < $2


echo -n "=== done ==========================="; date

