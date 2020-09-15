#!/bin/sh

# - pre exec -
module load miniconda-3
conda activate $HOME/ve.rp

$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf

export RADICAL_PILOT_DBURL="mongodb://rct:jdWeRT634k@`hostname -f`:59361/rct_db"
export RADICAL_LOG_LVL="DEBUG"
export RADICAL_PROFILE="TRUE"

# - exec -
$HOME/DrugWorkflows/workflow-0/wf0_oe_theta/wf0.py wf0.theta.cfg receptors.dat

# - post exec -
$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf --shutdown
