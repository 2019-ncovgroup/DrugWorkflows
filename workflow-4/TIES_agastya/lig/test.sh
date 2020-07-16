#!/bin/bash
#BSUB -P chm155_001
#BSUB -W 0:05
#BSUB -nnodes 13
#BSUB -alloc_flags smt1
#BSUB -J NAMD_lig
#BSUB -o NAMD_lig.o%J
#BSUB -e NAMD_lig.e%J

module load spectrum-mpi
module load fftw

cd $MEMBERWORK/chm155/test_TIES/lig/replica-confs

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
for i in {1..6}; 
do
   mkdir -p ../LAMBDA_$l/replicas/rep$i/equilibration
   mkdir -p ../LAMBDA_$l/replicas/rep$i/simulation
done
done
 
for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n6 -p6 -r6 -g0 -c7 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 7 +pemap 0-83:4,88-171:4 +commap 0,28,56,88,116,144 +replicas 6 --tclmain eq0-replicas.conf $l &
done
wait 

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n6 -p6 -r6 -g0 -c7 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 7 +pemap 0-83:4,88-171:4 +commap 0,28,56,88,116,144 +replicas 6 --tclmain eq1-replicas.conf $l &
done
wait 

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n6 -p6 -r6 -g0 -c7 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 7 +pemap 0-83:4,88-171:4 +commap 0,28,56,88,116,144 +replicas 6 --tclmain sim1-replicas.conf $l &
done
wait 


