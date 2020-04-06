# Workflow-3

## ESMACS

## Run with Radical Cybertools

### replica of raw_submission_esmacs.sh

```
python wf3.py --task esmacs
```

### replica of raw_submission_sim.sh

```
python wf3.py --task sim
```

### esmacs_analysis

```
python wf3.py --task esmacs_analysis
```


## Installation

### Conda on Summit

```
. "/sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh"
conda create -n wf-3 python=3.6
conda activate wf-3
```

### Radical Cybertools

```
pip install radical.entk
```

### mpi4py
```
conda install mpi4py -y
```

### Ambertools19

```
module load gcc/6.4.0
module load cuda/10.1.243
export CUDA_HOME=/sw/summit/cuda/10.1.243

# download AmberTools.tar.bz2 to summit
wget 'https://ambermd.org/cgi-bin/AmberTools19-get.pl?filename=AmberTools19.tar.bz2&Name=<ALBERT EINSTEIN>&Institution=<ETH>&City=<NYC>&State=<NA>&Country=<SWITZERLAND>'
# unzip
tar -xvjf AmberTools.tar.bz2

cd amber18

# first part without CUDA
LANG=en_US.UTF-8 CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse gnu
make -j 40 install

# now CUDA part
./configure --with-python `which python` -nofftw3 --no-updates -cuda -nosse gnu
export LD_LIBRARY_PATH="/sw/summit/cuda/10.1.243/lib:${LD_LIBRARY_PATH}"
make -j 40 install

#Then, add the IBM MPI:
module load spectrum-mpi/10.3.1.2-20200121
# this one is compatible with the gcc 6.4.0

# compile the -mpi version:
# first part without CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse -mpi gnu
make -j 40 install

# ps. note that it is possible to also compile the combination of -mpi and -cuda. It might be a good idea to have it too:
# with CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse -mpi -cuda gnu
make -j 40 install
```
