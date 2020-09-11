# workflow-2

## with molecules for pytorch resnet

[README](../../wf2/molecules/workflow-2/README_molecules.md)

## Availability

| System      | HPC Resource    | Status | Available date from |
| ----------- | --------------- | ------ | ------------------- |
| adrp        | longhorn        | Ready  | May 12th, 2020 |
| plpro       | longhorn        | -      | |
| adrp        | lassen          | Ready  | May 28th, 2020 |
| plpro       | lassen          | -      | |
| adrp        | summit          | Ready  | |
| plpro       | summit          | Ready* | May 12th, 2020 |

*plpro is waiting for new implementation of CVAE

## Instruction and Branch

Use a branch to isolate a system without affecting others in the workflow-2. Each branch has separate README and a python script to run.

| System | HPC | Document | Branch | Run | 
| ------ | --- | ------ | ------ | --- |
| adrp   | longhorn | [README](../../wf2/adrp/workflow-2/readme_longhorn.md) | [wf2/adrp branch](../../wf2/adrp/workflow-2) | `python longhorn_adrp.py` |
| adrp   | lassen | [README](../../wf2/adrp/workflow-2/readme_lassen.md) | [wf2/adrp branch](../../wf2/adrp/workflow-2) | `python lassen_adrp.py` |
| adrp   | summit | [README](../../wf2/adrp/workflow-2/README.md) | [wf2/adrp branch](../../wf2/adrp/workflow-2) | `python summit_md.py` |
| plpro   | summit | [README](../../wf2/plpro/workflow-2/README.md) | [wf2/plpro branch](../../wf2/plpro/workflow-2) | `python summit_md.py` |

## Installation

### Tensorflow/Keras and others (Summit)

```
(python3)
. "/sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh"
conda create -n workflow-2 python=3.6 -y
conda activate workflow-2
conda install tensorflow-gpu keras scikit-learn swig numpy cython scipy matplotlib pytables h5py -y
pip install MDAnalysis MDAnalysisTests parmed
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade
```

### OpenMM

by source code (for linux ppc64le e.g. Summit)
https://gist.github.com/lee212/4bbfe520c8003fbb91929731b8ea8a1e

by conda (for linux 64 e.g. PSC Bridges)
```
module load anaconda3
module load cuda/9.2
source /opt/packages/anaconda/anaconda3-5.2.0/etc/profile.d/conda.sh
conda install -c omnia-dev/label/cuda92 openmm
```

### Latest stack info

The following versions are verified on Summit for sucessful run of workflow-2

```
$ radical-stack

  ...
  
  radical.entk         : 1.0.2
  radical.pilot        : 1.2.1
  radical.saga         : 1.2.0
  radical.utils        : 1.2.2
```

### Shell variables

#### RMQ (Mandatory)

```
export RMQ_HOSTNAME=two.radical-project.org; export RMQ_PORT=33239
```

#### Profiling (Optional)

Profiling produces `*.json` and `*.prof` for additional info, if the following variables defined.

```
export RADICAL_PILOT_PROFILE=TRUE; 
export RADICAL_ENTK_PROFILE=TRUE 
```

## Run

It will require writable space before running the main script. Output files are stored in sub-directories. Locate the wf-2 repo at $MEMBERWORK/{{PROJECTID}}/ and run the script on Summit. $HOME becomes readable only system when a job is running.

```
$ python summit_md.py
```


## Prerequisites

Configurations in the script (`summit_md.py`)
- `md_counts`: a number of md simulations
- `ml_counts`: a number of CVAE
- `conda_path`: a location of the conda environment for openMM e.g. '$HOME/.conda/envs/openmm'
- `MAX_STAGE`: a number of iterations to stop
- `RETRAIN_FREQ`: an interval to trigger CVAE stage
- `LEN_initial`: a timesteps of the first MD run (nanosecond)
- `LEN_iter`: a timespan of the rest simulation trajectory (nanosecond)
- `generate_MD_stage(num_MD=N)`: a method with a N number of simulations
- `generate_ML_stage(num_ML=M)`: a method with a M number of training

Resource configurations in the script (`summit_md.py`)
- `res_dict` would have:
   - 'resource': HPC resource e.g. 'ornl.summit'
   - 'queue':
      - 'batch' for upto 2 hours TTX at `ornl.summit`
      - 'killable' for upto 1 day(24hours) TTX at `ornl.summit`
   - 'gpus': a number of GPU cores equal to N simulations (1 MD/ML run: 1GPU)

Bash environment variable for EnTK
- RMQ_HOSTNAME/RMQ_PORT (mandatory)
- export RADICAL_LOG_TGT=radical.log; export RADICAL_LOG_LVL=DEBUG (optional for extra log messages)
- export RADICAL_PILOT_PROFILE=TRUE; export RADICAL_ENTK_PROFILE=TRUE (optional for profiling)


## Clean up

Intermediate files/folders are generated over the workflow execution. These need to be deleted before the next run.
Currently, manual deletion is required like:
```
rm -rf CVAE_exps/cvae_runs_*
rm -rf MD_exps/VHP_exp/omm_runs_*
rm -rf MD_exps/fs-pep/omm_runs_*
rm -rf Outlier_search/outlier_pdbs/*
rm -rf Outlier_search/eps_record.json
rm -rf Outlier_search/restart_points.json
```

