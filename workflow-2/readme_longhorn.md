`updated on: 03-22-2020`

# Longhorn for workflow-2


## Environment installation

```bash
module load gcc/7.3.0

export PYTHONNOUSERSITE=True
export PREFIX=$HOME
wget -q https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-ppc64le.sh -O ~/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels conda-forge \
             --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101 \
             --add channels anaconda
conda create -y -n covid-19-2 python=3.6
conda activate covid-19-2

conda install -y -c anaconda tensorflow-gpu
conda install -y cython keras scikit-learn swig scipy matplotlib pytables h5py
conda install -y openmm=7.4.0=py36_cuda101_0
pip install MDAnalysis MDAnalysisTests parmed
```

## RCT installation
*NOTE:* picked branches might be changed according to the latest updates

```bash
pip install radical.utils==1.2.2
pip install git+https://github.com/radical-cybertools/radical.saga.git@hotfix/longhorn
pip install git+https://github.com/radical-cybertools/radical.pilot.git@fix/srun_placement
pip install radical.entk
```

## DrugWorkflows dev-code

```bash
git clone --single-branch --branch devel https://github.com/2019-ncovgroup/DrugWorkflows.git
cd DrugWorkflows/workflow-2
```

## Changes in `summit_md.py`

Paths and corresponding updates for tasks parameters
```python
conda_base_path = f'{os.environ.get("HOME")}/.miniconda3'
conda_path = f'{conda_base_path}/envs/covid-19-2'

TASK_PRE_EXEC_BASE = [
    'source %s/bin/activate' % conda_base_path,
    'conda activate %s' % conda_path]
TASK_PRE_EXEC_MODULES = [
    'module load gcc/7.3.0',
    'module load openmpi/3.1.2',
    'module load cuda/10.1']

...
t1.pre_exec = TASK_PRE_EXEC_BASE + TASK_PRE_EXEC_MODULES
... 
t2.pre_exec = TASK_PRE_EXEC_BASE
...
t3.pre_exec = TASK_PRE_EXEC_BASE + TASK_PRE_EXEC_MODULES
...
t4.pre_exec = TASK_PRE_EXEC_BASE + TASK_PRE_EXEC_MODULES
```

```python
import radical.pilot as rp

t1/3/4.cpu_reqs = {...
                   'process_type': rp.MPI,
                   ...}
```

Longhorn resource description
```python
NODE_COUNTS = 2
res_dict = {'resource': 'xsede.longhorn',
            'project': 'FTA-Jha',
            'queue': 'v100',
            'schema': 'local',
            'walltime': 60 * 6,
            'cpus': 40 * NODE_COUNTS,
            'gpus': 4 * NODE_COUNTS}
```

## Pre-run env-settings

```bash
export RMQ_HOSTNAME=two.radical-project.org 
export RMQ_PORT=33239
export RADICAL_PILOT_PROFILE=True
export RADICAL_ENTK_PROFILE=True

export RADICAL_LOG_TGT=radical.log
export RADICAL_LOG_LVL=DEBUG
```
