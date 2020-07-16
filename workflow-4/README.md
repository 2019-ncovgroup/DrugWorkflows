# Workflow-4 in RADICAL EnTK

## Workflow Description

This repository includes workflow-4 scripts written in Python using [RADICAL Cybertools](https://radical-cybertools.github.io/) (specifically Ensemble Toolkit), as an implementation of the TIES protocol with [NAMD](https://www.ks.uiuc.edu/Research/namd/) to perform simulation of large biomolecular systems.

## Installation (Summit @ ORNL)

### RADICAL Cybertools (using Python Virtual Environment)

```
(python3 in user space for installation permission)
. /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
conda create -n wf4 python=3.7 -y
conda activate wf4
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade
```

### Environmental Variables (RabbitMQ and MongoDB)

```
export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERNAME=<your username>
export RMQ_PASSWORD=<your password>
export RADICAL_PILOT_DBURL="mongodb://<your username>:<your password>@129.114.17.185:27017/rct-test"
```

Note that installation of the NAMD binaries on Summit are not needed, since we are using pre-installed binaries in shared locations from other efforts.

## Run

The main script requires to be placed at a writable space before running. Output files are stored in sub-directories of the current directory. Locate this code repository at $MEMBERWORK/{{PROJECTID}}/ and run the script there. $HOME directory does not work when running the script since it becomes a read-only filesystem when a job is running.

```
$ . /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
$ conda activate wf4
$ python workflow-4.py
```

## Performance

1. Use average time to completion (TTX) of workflows running on Summit, unit: minute.
2. Use JSRUN performance numbers as the baseline.

| System        | baseline | RCT EnTK | Slowdown |
| ------------- | -------- | -------- | -------- |
| com (65-node) |     14.2 |          |          |
| lig (13-node) |     13.7 |          |          |
