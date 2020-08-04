#!/bin/sh


# ------------------------------------------------------------------------------
ID="$1"
SMILES="$2"

FMT=$(/tmp/tools/DataCrunching/ProcessingScripts/Autodock/echo_smiles.py "$SMILES")

BOX="/tmp/sbox_$ID"
mkdir -p "$BOX"

echo "$ID - $SMILES - start ($BOX) ($(obabel -V))"

echo "$FMT" \
    | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2  \
    > "$BOX/$ID.mol2"

echo "$ID - $SMILES - stop ($BOX/$ID.mol2)"

