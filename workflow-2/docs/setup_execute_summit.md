# Setup and Execute W2 on Summit from Summit Login Nodes

## SSH 

```
ssh $USER@summit.olcf.ornl.gov
```

## Setup on envs

```
export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERNAME=****
export RMQ_PASSWORD=****
export RADICAL_PILOT_DBURL="mongodb://$RMQ_USERNAME:$RMQ_PASSWORD@$RMQ_HOSTNAME/hyperrct"

export CONDA_OPENMM=/gpfs/alpine/proj-shared/med110/conda/openmm
export CONDA_PYTORCH=/gpfs/alpine/proj-shared/med110/atrifan/scripts/pytorch-1.6.0_cudnn-8.0.2.39_nccl-2.7.8-1_static_mlperf
export MOLECULES_PATH=/gpfs/alpine/proj-shared/med110/hrlee/git/braceal/molecules

. "/sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh"
conda activate WF2
```

## Setup on Project
```
export PROJ=med110
```

## Setup on Working Directory
```
cd $MEMBERWORK/$PROJ/DrugWorkflows/workflow-2
export WF2_BASE_PATH=`pwd`
```

## Setup on Intermediate/Result Data

```
# clean up
rm -rf $WF2_BASE_PATH/MD_exps/*/omm_runs_*
rm -rf $WF2_BASE_PATH/MD_to_CVAE/cvae_input.h5
rm -rf $WF2_BASE_PATH/CVAE_exps/model-cvae_runs_*
rm -rf $WF2_BASE_PATH/Outlier_search/outlier_pdbs/*
rm -rf $WF2_BASE_PATH/Outlier_search/eps_record.json
rm -rf $WF2_BASE_PATH/Outlier_search/restart_points.json

```

## Setup on Parameters

manual change in the script

- project_name: project name
- wall_hour: walltime in hour
- md_counts: simulation concurrent numbers
- ml_counts: training concurrent numbers
- protein: system name to recognize, i.e. sub-directory name 
- pdb_path: pdb file path
- ref_path: reference file path
- CUR_STAGE: start index
- MAX_STAGE: stop index
- RETRAIN_FREQ: training interval
- LEN_initial: simulation steps in nanoseconds for initial run
- LEN_iter: simulation steps in nanoseconds for rest


## Execute

~~python summit_md_molecules.py~~
```
python molecules.py 3clpro_system.json
```

## Save results for further analysis
```
export CUR_TIME=`date +%Y-%m-%d-%H:%M:%S`
mkdir -p $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/MD_exps/*/omm_runs_* $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/MD_to_CVAE/cvae_input.h5 $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/CVAE_exps/model-cvae_runs_* $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/Outlier_search/outlier_pdbs/* $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/Outlier_search/eps_record.json $WF2_BASE_PATH/results/$CUR_TIME
mv $WF2_BASE_PATH/Outlier_search/restart_points.json $WF2_BASE_PATH/results/$CUR_TIME
```



```
