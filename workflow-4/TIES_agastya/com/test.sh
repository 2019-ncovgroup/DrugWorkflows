#!/bin/bash
#BSUB -P chm155_001
#BSUB -W 0:05
#BSUB -nnodes 65
#BSUB -alloc_flags smt1
#BSUB -J NAMD_com
#BSUB -o NAMD_com.o%J
#BSUB -e NAMD_com.e%J

module load spectrum-mpi
module load fftw

cd $MEMBERWORK/chm155/test_TIES/com/replica-confs

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
for i in {1..5}; 
do
   mkdir -p ../LAMBDA_$l/replicas/rep$i/equilibration
   mkdir -p ../LAMBDA_$l/replicas/rep$i/simulation
done
done
 
for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n5 -p5 -r1 -g0 -c42 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 42 +pemap 0-83:4,88-171:4 +commap 0 +replicas 5 --tclmain eq0-replicas.conf $l &
done
wait 

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n5 -p5 -r1 -g0 -c42 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 42 +pemap 0-83:4,88-171:4 +commap 0 +replicas 5 --tclmain eq1-replicas.conf $l &
done
wait 

for l in 0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00; do
   jsrun --bind rs -n5 -p5 -r1 -g0 -c42 /gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2 +ppn 42 +pemap 0-83:4,88-171:4 +commap 0 +replicas 5 --tclmain sim1-replicas.conf $l &
done
wait 

