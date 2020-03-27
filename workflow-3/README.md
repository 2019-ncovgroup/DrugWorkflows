# Workflow-3

## ESMACS

## Installation

### Ambertools19

```
module load gcc/6.4.0
module load cuda/10.1.243
export CUDA_HOME=/sw/summit/cuda/10.1.243

# install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-ppc64le.sh
sh Miniconda2-latest-Linux-ppc64le.sh

# check the link to your conda python, e.g.
# does the python work fine?
/ccs/home/dresio/miniconda2/bin/python2.7

# download (scp or rsync) AmberTools.tar.bz2 to summit
# unzip
bzip2 -d AmberTools.tar.bz2
# open the tar
tar xvf AmberTools.tar.bz2

cd amber18

# first part without CUDA
LANG=en_US.UTF-8 CC=gcc CXX=g++ FC=gfortran ./configure --with-python /ccs/home/dresio/miniconda2/bin/python2.7 -nofftw3 --no-updates -nosse gnu
make -j 8 install

# now CUDA part
./configure --with-python /ccs/home/dresio/miniconda2/bin/python2.7 -nofftw3 --no-updates -cuda -nosse gnu
export LD_LIBRARY_PATH="/sw/summit/cuda/10.1.243/lib:${LD_LIBRARY_PATH}"
make -j 8 install

#Then, add the IBM MPI:
module load spectrum-mpi/10.3.1.2-20200121
# this one is compatible with the gcc 6.4.0

# compile the -mpi version:
# first part without CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python /ccs/home/dresio/miniconda2/bin/python2.7 -nofftw3 --no-updates -nosse -mpi gnu
make -j 8 install

# ps. note that it is possible to also compile the combination of -mpi and -cuda. It might be a good idea to have it too:
# with CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python /ccs/home/dresio/miniconda2/bin/python2.7 -nofftw3 --no-updates -nosse -mpi -cuda gnu
make -j 8 install
```
