`updated on: 04-20-2020`

# Longhorn for workflow-2


## Environment installation
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
pip install radical.pilot radical.entk
```

## DrugWorkflows dev-code
```shell script
git clone --single-branch --branch devel https://github.com/2019-ncovgroup/DrugWorkflows.git
cd DrugWorkflows/workflow-2
```

## Changes for resource config
```shell script
# for local copy: <path>/.radical/pilot/configs/resource_local.json
...
        "mpi_launch_method"           : "MPIRUN",
        "pre_bootstrap_0"             : ["module load gcc/7.3.0",
                                         "module load openmpi/3.1.2",
                                         "module --expert load xl",
                                         "source $HOME/.miniconda3/etc/profile.d/conda.sh"],
...
        "python_dist"                 : "anaconda",
        "virtenv"                     : "ve.rp",
        "virtenv_mode"                : "use",
        "rp_version"                  : "installed",
...
```

## Changes in `<resource_machine>_md.py`

Tasks parameters
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

Longhorn resource description
```python
NODE_COUNTS = 2
res_dict = {'resource': 'local.longhorn',
            'project': 'FTA-Jha',
            'queue': 'development',
            'schema': 'local',
            'walltime': 60 * 2,  # max 2 hours and 2 nodes for development queue
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
