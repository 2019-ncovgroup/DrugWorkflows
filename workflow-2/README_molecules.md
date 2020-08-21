DeepDriveMD with molecules
==========================

Dependency
-----------

- molecules (https://github.com/braceal/molecules)
- pytorch

Run (fs-pep)
------------

```
export CONDA_OPENMM=/gpfs/alpine/proj-shared/med110/conda/openmm
export CONDA_PYTORCH=/gpfs/alpine/proj-shared/med110/atrifan/scripts/pytorch-1.6.0_cudnn-8.0.2.39_nccl-2.7.8-1_static_mlperf
export MOLECULES_PATH=/gpfs/alpine/proj-shared/med110/hrlee/git/braceal/molecules

python summit_md_molecules.py
```
