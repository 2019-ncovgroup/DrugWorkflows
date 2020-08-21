# Deploy W0 on Comet

Assumes launching it via gsissh from the RADICAL jetstream machine.

```
ssh w0comet@129.114.17.185
```

## Deploy RCT on 129.114.17.185

```
export PYTHONNOUSERSITE=True
export PREFIX=$HOME
export WF0_CONDA_ENV=ve.rp
mkdir -p $PREFIX
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels conda-forge
conda update --yes --all
conda create --yes -n $WF0_CONDA_ENV
conda activate $WF0_CONDA_ENV
conda install --yes apache-libcloud msgpack-python pyzmq munch regex netifaces \
                    colorama pymongo python-hostlist setproctitle ntplib pytest \
                    pylint flake8 coverage mock wheel future setproctitle pudb parse
pip install git+https://github.com/radical-cybertools/radical.utils.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.saga.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.pilot.git@project/covid-19
```

## Deploy RCT on Comet

```
myproxy-logon -s myproxy.xsede.org -l user_name -t 72
gsissh comet.sdsc.xsede.org
cd /oasis/scratch/comet/$USER/temp_project/radical.pilot.sandbox
mkdir old; mv * old/

export PYTHONNOUSERSITE=True
export PREFIX=/oasis/scratch/comet/$USER/temp_project/radical.pilot.sandbox
export WF0_CONDA_ENV=ve.rp

mkdir -p $PREFIX
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda config --add channels conda-forge \
             --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101
conda update --yes --all
conda create --yes -n $WF0_CONDA_ENV
conda activate $WF0_CONDA_ENV
conda install --yes cudatoolkit=10.1.243
conda install --yes atomicwrites attrs blas fftw3f importlib_metadata libtiff \
                    more-itertools ninja olefile packaging pillow pluggy py pytest pandas psutil \
                    docopt setproctitle pymbar openmm
conda install --yes -c openeye openeye-toolkits
conda install --yes apache-libcloud msgpack-python pyzmq munch regex netifaces \
                    colorama pymongo python-hostlist setproctitle ntplib pytest \
                    pylint flake8 coverage mock wheel future setproctitle pudb parse
pip install git+https://github.com/radical-cybertools/radical.utils.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.saga.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.pilot.git@project/covid-19
```

# Deploy W0 repository on Comet

```
cd /oasis/scratch/comet/$USER/temp_project/radical.pilot.sandbox
git clone --single-branch --branch covid https://github.com/aclyde11/Model-generation.git
git clone --single-branch --branch devel https://github.com/2019-ncovgroup/DrugWorfklows.git
```
```
