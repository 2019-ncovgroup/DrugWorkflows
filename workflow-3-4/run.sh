#!/bin/bash

# ESMACS (OpenMM simulation) + TIES (com)
python workflow-3-4.py -t sim_com -i /gpfs/alpine/scratch/litan/med110/inpath

# ESMACS (OpenMM simulation) + TIES (lig)
python workflow-3-4.py -t sim_lig -i /gpfs/alpine/scratch/litan/med110/inpath
