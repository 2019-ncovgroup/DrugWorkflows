# workflow-3-4 (hybridwf) in RADICAL EnTK

## Workflow Description

This repository includes the workflow script which merges workflow-3 and workflow-4 written in Python using [RADICAL Cybertools](https://radical-cybertools.github.io/) (specifically the Ensemble Toolkit), as an implementation of the ESMACS protocol with [OpenMM](http://openmm.org/) and the TIES protocol with [NAMD](https://www.ks.uiuc.edu/Research/namd/) to perform equilibration and simulation of large biomolecular systems.

## Installation

### RADICAL Cybertools (using Conda and Python Virtual Environment)

```
. /sw/summit/python/3.7/anaconda3/5.3.0/etc/profile.d/conda.sh
conda create -n hybridwf python=3.7 -y
conda activate hybridwf
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade
```

### ESMACS Tasks Setup

Warning: the parameters exported in the following code must be the same used 
for `hybridwf.py` in the `esmacs` method of the `EsmacsTies` class. You will 
have to edit `hybridwf.py` accordingly.

```
export PROJ="med110"
export CONDA_ENV="workflow-3-4"
export BASE_DIR="$MEMBERWORK/$PROJ/"
export RUN_DIR="$BASE_DIR/wf3"

cd $BASE_DIR
mkdir $RUN_DIR
git clone git@github.com:2019-ncovgroup/DrugWorkflows.git
cp -rp DrugWorkflows/workflow-3-4/input $RUN_DIR

. /sw/summit/python/3.7/anaconda3/5.3.0/etc/profile.d/conda.sh
conda create -n $CONDA_ENV python=3.7 -y
conda activate $CONDA_ENV
# install OpenMM (via conda on Summit)
```

### OpenMM

- by source code (for Linux ppc64le)
https://gist.github.com/lee212/4bbfe520c8003fbb91929731b8ea8a1e

- by conda (for Linux x86\_64, e.g., PSC Bridges)
```
module load anaconda3
module load cuda/9.2
source /opt/packages/anaconda/anaconda3-5.2.0/etc/profile.d/conda.sh
conda install -c omnia/label/cuda92 openmm
```
- by conda on Summit. Assuming you have already created and activated a 
  conda env following the instructions at `ESMACS Tasks Setup`:
```
module load cuda/9.2
conda install -c omnia-dev/label/cuda92 -y openmm
```


### Environmental Variables (RabbitMQ and MongoDB)

```
export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERNAME=<your username>
export RMQ_PASSWORD=<your password>
export RADICAL_PILOT_DBURL="mongodb://<your username>:<your password>@129.114.17.185:27017/rct-test"
```

Note that our workflow uses NAMD, but installation of the NAMD binaries on Summit are not needed, since we are using pre-installed binaries in shared locations from other efforts.

## Run

The main script requires to be placed at a writable space before running. Output files are stored in sub-directories of the current directory. Locate this code repository at `$MEMBERWORK/{{PROJECTID}}/` and run the script there. `$HOME` directory does not work when running the script since it becomes a read-only filesystem when a job is running.

Note that `-t` parameter specifies the type of workflow to run, and the `-n` parameter specifies the number of nodes requested to run the workflow.

- workflow-3 only
```
$ python hybridwf.py -t wf3 -n 4
```
- workflow-4 only (com)
```
$ python hybridwf.py -t wf4_com -n 65
```
- workflow-4 only (lig)
```
$ python hybridwf.py -t wf4_lig -n 13
```
- hybrid workflow-3 and workflow-4 (com)
```
$ python hybridwf.py -t hybridwf_com -n 65
```
- hybrid workflow-3 and workflow-4 (lig)
```
$ python hybridwf.py -t hybridwf_lig -n 13
```
