`updated on: 05-01-2020`

# Longhorn@TACC for workflow-2

## Environment installation
```shell script
module load conda/4.8.3
conda create --name rp --clone py3_powerai_1.6.1
conda activate rp
conda config --set allow_conda_downgrades true
conda config --set channel_priority false
conda install -c conda-forge -y swig
conda install -c anaconda -y pytables=3.4.4
# https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/
# release 1.6.1 contains keras of correct version for WF2 (<=2.2.4)
conda install -y keras=2.2.4
conda config --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101
conda install -y openmm=7.4.0=py36_cuda101_0
pip install MDAnalysis MDAnalysisTests parmed
pip install numpy==1.16.1
```

```shell script
# seems that loading this module is not needed at the env setup stage
# module load gcc/7.3.0
```

OBSOLETE env setup steps
```shell script
module load gcc/7.3.0

export PYTHONNOUSERSITE=True

wget -q https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-ppc64le.sh -O ~/miniconda.sh
chmod +x $HOME/miniconda.sh
$HOME/miniconda.sh -b -p $HOME/.miniconda3
source $HOME/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels conda-forge \
             --add channels omnia/label/cuda101 \
             --add channels omnia-dev/label/cuda101 \
             --add channels anaconda
conda create -y -n ve.rp python=3.6
conda activate ve.rp

conda install -y cython scikit-learn swig scipy matplotlib pytables h5py
conda install -y -c anaconda tensorflow-gpu'<2.0.0'
conda install -y keras'<=2.2.4'
conda install -y openmm=7.4.0=py36_cuda101_0
pip install MDAnalysis MDAnalysisTests parmed
```

## RCT installation
```shell script
pip install git+https://github.com/radical-cybertools/radical.utils.git@devel 
pip install git+https://github.com/radical-cybertools/radical.saga.git@devel
pip install git+https://github.com/radical-cybertools/radical.pilot.git@devel
pip install git+https://github.com/radical-cybertools/radical.entk.git@devel
```

## DrugWorkflows dev-code
```shell script
git clone --single-branch --branch devel https://github.com/2019-ncovgroup/DrugWorkflows.git
cd DrugWorkflows/workflow-2
```

## Changes in resource config `<path>/.radical/pilot/configs/resource_local.json`
```shell script
# python and virtual environment
        "python_dist"                 : "anaconda",
        "virtenv"                     : "$SCRATCH/conda_envs/rp",
        "virtenv_mode"                : "use",
        "rp_version"                  : "installed",
```
```shell script
# MPIRUN (initial setup - will be obsolete later)
        "task_launch_method"          : "MPIRUN",
        "mpi_launch_method"           : "MPIRUN",
        "pre_bootstrap_0"             : ["module load gcc/7.3.0",
                                         "module load openmpi/3.1.2",
                                         "module --expert load xl",
                                         "module load conda/4.8.3"],
```
```shell script
# MPIRUN
```
```shell script
# IBRUN
```

## Changes in `<resource_machine>_md.py`
Tasks parameters (`MPIRUN` version)
```python
TASK_PRE_EXEC_MODULES = [
    'module load cuda/10.1',
    'export OMPI_LD_PRELOAD_POSTPEND_DISTRO=/opt/ibm/spectrum_mpi/lib/libpami_cudahook.so',
    'export LD_PRELOAD="/opt/ibm/spectrum_mpi/lib/pami_noib/libpami.so $OMPI_LD_PRELOAD_POSTPEND_DISTRO $LD_PRELOAD"']
TASK_PRE_EXEC_ENV = [
    "export TACC_SPECTRUM_ENV=`/usr/local/bin/build_env.pl | sed -e's/\(\S\S*\)=\S\S* / -x \\1/g'`"]
...
t1.pre_exec = TASK_PRE_EXEC_MODULES + ... + TASK_PRE_EXEC_ENV
t1.executable = ['$TACC_SPECTRUM_ENV python']
t3.pre_exec = TASK_PRE_EXEC_MODULES + ... + TASK_PRE_EXEC_ENV
t3.executable = ['$TACC_SPECTRUM_ENV python']
t4.pre_exec = TASK_PRE_EXEC_MODULES + ... + TASK_PRE_EXEC_ENV
t4.executable = ['$TACC_SPECTRUM_ENV python']
```
Tasks parameters (`IBRUN` version)
```python
```

Longhorn resource description
```python
NODE_COUNTS = 2
res_dict = {'resource': 'local.longhorn',
            'project': 'FTA-Jha',
            'queue': 'development',  # other queues: v100, v100-lm
            'schema': 'local',
            'walltime': 60 * 2,  # max 2 hours and 2 nodes for development queue
            'cpus': 40 * NODE_COUNTS,
            'gpus': 4 * NODE_COUNTS}
```

## Pre-run env-settings

```shell script
module load conda/4.8.3
conda activate $SCRATCH/conda_envs/rp

export RMQ_HOSTNAME=two.radical-project.org 
export RMQ_PORT=33239

export RADICAL_LOG_TGT=radical.log
export RADICAL_LOG_LVL=DEBUG
```
