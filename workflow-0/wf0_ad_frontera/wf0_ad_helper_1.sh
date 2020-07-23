#!/bin/sh


# ------------------------------------------------------------------------------
ID="$1"
SMILES="$2"

BOX="/tmp/sbox_$ID"
mkdir "$BOX"

echo "$ID - $SMILES - start ($BOX)" >> /tmp/t

/tmp/tools/DataCrunching/ProcessingScripts/Autodock/echo_smiles.py "$SMILES" \
    | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2  \
    > "$BOX/$ID.mol2"

echo "$ID - $SMILES - stop ($BOX/$ID.mol2)" >> /tmp/t

