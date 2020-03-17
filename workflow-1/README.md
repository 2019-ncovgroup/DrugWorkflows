## Create a conda environment on Summit

```
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-ppc64le.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels omnia \
             --add channels conda-forge \
             --add channels omnia/label/cuda101 \
             --add channels omnia-dev \
             --add channels defaults \
             --add channels acellera \
             --add channels psi4 \
             --add channels openeye \
             --add channels pytorch
conda update --yes --all
conda create -n covid-19-1
conda activate covid-19-1
conda install --yes ambertools atomicwrites attrs blas cudatoolkit fftw3f importlib_metadata libtiff \
                    more-itertools ninja olefile packaging pillow pluggy py pytest pandas psutil \
                    docopt setproctitle pymbar 
conda install --yes -c omnia-dev/label/cuda101 openmm

# Incompatible platform power9 Vs intel
# - mkl_fft
# - intel-openmp
# - libgcc
# - mkl
# - mkl-service
# - mkl_random

# not available for ppc in conda/pip
# - ambermini
# - openeye-toolkits
# - packmol-memgen

# already satisfied in pip not in conda
# - parmed 
# - pdb4amber 
# - pymsmt
# - pytraj
# - sander

# Available only for p3.6 if necessary
# - pytorch
# - torchvision
# conda install --yes -c jjhelmus pytorch torchvision

```
