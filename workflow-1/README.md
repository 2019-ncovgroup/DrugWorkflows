## Create a conda environment on Summit

The following creates a conda environment as similar as possible to the one create for workflow-0. Lists of incompatible or missing packages below.

```
PREFIX=$HOME
module purge
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-ppc64le.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels defaults \
             --add channels conda-forge \
             --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101
conda update --yes --all
conda create -y -n covid-19-1
conda activate covid-19-1
conda install --yes atomicwrites attrs blas cudatoolkit fftw3f importlib_metadata libtiff \
                    more-itertools ninja olefile packaging pillow pluggy py pytest pandas psutil \
                    docopt setproctitle pymbar openmm

# Must use branch covid of Model-generation
git clone --single-branch --branch covid https://github.com/aclyde11/Model-generation.git
```
### May be needed in the future
- tqdm
- ambertools

### Incompatible platform power9 Vs intel
- mkl_fft
- intel-openmp
- libgcc
- mkl
- mkl-service
- mkl_random

### not available for ppc in conda/pip
- ambermini
- openeye-toolkits
- packmol-memgen

### already satisfied in pip not in conda
- parmed 
- pdb4amber 
- pymsmt
- pytraj
- sander

### Available only for p3.6 if necessary
- pytorch
- torchvision
```
conda install --yes -c jjhelmus pytorch torchvision

# fetch data set
cd $PREFIX
wget https://www.dropbox.com/s/74ukvsx5888p79a/adpr_ena_db.tar.gz?dl=0 -O $PREFIX/adpr_ena_db.tar.gz
tar zxvf adpr_ena_db.tar.gz
rm adpr_ena_db.tar.gz

# Note that the application needs `module load cuda` to run

export RADICAL_PILOT_DBURL=mongodb://giannis:radicalpass@149.165.170.227:29019/radical

```
