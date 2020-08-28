# Workflow-3-4 (hybridwf) in RADICAL EnTK

## Workflow Description

This repository includes the workflow script which merges workflow-3 and workflow-4 written in Python using [RADICAL Cybertools](https://radical-cybertools.github.io/) (specifically the Ensemble Toolkit), as an implementation of the ESMACS protocal with [OpenMM](http://openmm.org/) and the TIES protocol with [NAMD](https://www.ks.uiuc.edu/Research/namd/) to perform equilibration and simulation of large biomolecular systems.

## Installation (Summit @ ORNL)

### RADICAL Cybertools (using Python Virtual Environment)

```
(python3 in user space for installation permission)
. /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
conda create -n hybridwf python=3.7 -y
conda activate hybridwf
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade
```

### OpenMM

- by source code (for Linux ppc64le, e.g., Summit)
https://gist.github.com/lee212/4bbfe520c8003fbb91929731b8ea8a1e

- by conda (for Linux x86\_64, e.g., PSC Bridges)
```
module load anaconda3
module load cuda/9.2
source /opt/packages/anaconda/anaconda3-5.2.0/etc/profile.d/conda.sh
conda install -c omnia/label/cuda92 openmm
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

The main script requires to be placed at a writable space before running. Output files are stored in sub-directories of the current directory. Locate this code repository at $MEMBERWORK/{{PROJECTID}}/ and run the script there. $HOME directory does not work when running the script since it becomes a read-only filesystem when a job is running.

```
- workflow-3 only
$ python workflow-4.py -t com
- workflow-4 only (com)
$ python workflow-4.py -t lig
- workflow-4 only (lig)                                                                                                $ python workflow-4.py -t lig
- hybrid workflow-3 and workflow-4 (com)
$ python workflow-4.py -t lig
- hybrid workflow-3 and workflow-4 (lig)
$ python workflow-4.py -t lig
```
