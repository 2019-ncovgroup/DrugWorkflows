`updated on: 05-28-2020`

# Lassen@LLNL

## Test result of ADRP

```
ls /p/gpfs1/titov1/to_share
eps_record.json           omm_runs_adrp_1589843465  omm_runs_adrp_1589844391  omm_runs_adrp_1589847656  omm_runs_adrp_1590350779      omm_runs_rank1579_1590443308  omm_runs_rank2355_1590443314  omm_runs_rank2437_1590442128  omm_runs_rank2437_1590463593  omm_runs_rank941_1590446442  unit.000003  unit.000013
omm_runs_adrp_1589842585  omm_runs_adrp_1589843466  omm_runs_adrp_1589845339  omm_runs_adrp_1589847657  omm_runs_adrp_1590442123      omm_runs_rank1579_1590446439  omm_runs_rank2355_1590446440  omm_runs_rank2437_1590442129  omm_runs_rank2437_1590463594  omm_runs_rank941_1590462101  unit.000004
omm_runs_adrp_1589842586  omm_runs_adrp_1589843468  omm_runs_adrp_1589845340  omm_runs_adrp_1589847658  omm_runs_adrp_1590443307      omm_runs_rank1579_1590462098  omm_runs_rank2355_1590446445  omm_runs_rank2437_1590443310  omm_runs_rank2437_1590465761  omm_runs_rank941_1590463592  unit.000005
omm_runs_adrp_1589842587  omm_runs_adrp_1589844384  omm_runs_adrp_1589845341  omm_runs_adrp_1589847659  omm_runs_adrp_1590446438      omm_runs_rank1579_1590463589  omm_runs_rank2355_1590462099  omm_runs_rank2437_1590443312  omm_runs_rank2437_1590465762  omm_runs_rank941_1590465760  unit.000006
omm_runs_adrp_1589842588  omm_runs_adrp_1589844385  omm_runs_adrp_1589845342  omm_runs_adrp_1589847660  omm_runs_adrp_1590462097      omm_runs_rank1579_1590465757  omm_runs_rank2355_1590463590  omm_runs_rank2437_1590443313  omm_runs_rank2437_1590688291  omm_runs_rank941_1590688292  unit.000007
omm_runs_adrp_1589842589  omm_runs_adrp_1589844386  omm_runs_adrp_1589845343  omm_runs_adrp_1589847661  omm_runs_adrp_1590463588      omm_runs_rank1579_1590688289  omm_runs_rank2355_1590465758  omm_runs_rank2437_1590446441  omm_runs_rank2437_1590688293  outlier_pdbs                 unit.000008
omm_runs_adrp_1589842590  omm_runs_adrp_1589844387  omm_runs_adrp_1589845344  omm_runs_adrp_1589847662  omm_runs_adrp_1590465756      omm_runs_rank2355_1590350776  omm_runs_rank2355_1590688290  omm_runs_rank2437_1590446443  omm_runs_rank2437_1590688294  restart_points.json          unit.000009
omm_runs_adrp_1589842591  omm_runs_adrp_1589844388  omm_runs_adrp_1589845345  omm_runs_adrp_1590350773  omm_runs_adrp_1590688288      omm_runs_rank2355_1590442125  omm_runs_rank2355_1590688295  omm_runs_rank2437_1590446444  omm_runs_rank941_1590350780   unit.000000                  unit.000010
omm_runs_adrp_1589842592  omm_runs_adrp_1589844389  omm_runs_adrp_1589845346  omm_runs_adrp_1590350775  omm_runs_rank1579_1590350774  omm_runs_rank2355_1590442130  omm_runs_rank2437_1590350778  omm_runs_rank2437_1590462102  omm_runs_rank941_1590442127   unit.000001                  unit.000011
omm_runs_adrp_1589843462  omm_runs_adrp_1589844390  omm_runs_adrp_1589847655  omm_runs_adrp_1590350777  omm_runs_rank1579_1590442124  omm_runs_rank2355_1590443309  omm_runs_rank2437_1590442126  omm_runs_rank2437_1590462103  omm_runs_rank941_1590443311   unit.000002                  unit.000012

```

## Login ([docs](https://lc.llnl.gov/confluence/display/LC/SSH+Guide+for+Livermore+Computing))
```shell script
ssh -l <lcusername> lassen.llnl.gov
```
GPFS work directory: `/p/gpfs1/$USER` (IBM's Spectrum Scale file system)
Bank: `cv19-a01` ("shares")

## Environment installation
- IBM PowerAI in LC: https://lc.llnl.gov/confluence/display/lc/ibm+powerai+in+lc
- Alternative (or at some points as additional) installation:
```shell script
export PREFIX=/p/gpfs1/$USER

wget -q https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-ppc64le.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda create -y -n ve.rp python=3.7
conda activate ve.rp

# in case of "CondaHTTPError: HTTP 000 CONNECTION FAILED for url <url>"
# use the following command: `conda config --set ssl_verify no`
```
WF2 packages (IBM Watson Machine Learning Community Edition | WML CE)
```shell script
conda config --add channels https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/
conda install -y -c https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/ cython scikit-learn scipy matplotlib h5py tensorflow-gpu
conda install -c conda-forge -y swig
conda install -c anaconda -y pytables
conda install -y keras

# cuda that corresponds WML CE should be used later: `module load cuda/10.2.89`

conda config --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101
conda install -y openmm=7.4.0=py37_cuda101_0

# if there is an error with installation of `gsd` package, 
# then `gcc` module should be loaded (`module load gcc/8.3.1`)
# *) this might mess with paths, thus need to re-activate conda-env again
pip install MDAnalysis MDAnalysisTests parmed

# package `typing` should be uninstalled, so the built-in one will be in use
# (causes an issue for python 3.7, and not for 3.6) 
# pip uninstall -y typing
```
RCT installation
```shell script
conda install pyzmq
```
```shell script
pip install git+https://github.com/radical-cybertools/radical.utils.git@devel
pip install git+https://github.com/radical-cybertools/radical.saga.git@devel
pip install git+https://github.com/radical-cybertools/radical.pilot.git@devel
pip install git+https://github.com/radical-cybertools/radical.entk.git@devel
```

## RADICAL-Pilot setup
User config dir: `mkdir -p $HOME/.radical/pilot/configs/`

Resource config file: `$HOME/.radical/pilot/configs/resource_llnl.json` 
(it overwrites pre-set configuration with our conda-env parameters):
```shell script
{
    "lassen": {
        "description"                 : "",
        "notes"                       : "",
        "schemas"                     : ["local"],
        "local"                       : 
        {
            "job_manager_hop"         : "fork://localhost/",
            "job_manager_endpoint"    : "lsf://localhost/",
            "filesystem_endpoint"     : "file://localhost/"
        },
        "forward_tunnel_endpoint"     : "`hostname -f`",
        "cores_per_node"              : 40,
        "gpus_per_node"               : 4,
        "sockets_per_node"            : 2,
        "default_queue"               : "pbatch",
        "resource_manager"            : "LSF_SUMMIT",
        "agent_scheduler"             : "CONTINUOUS",
        "agent_spawner"               : "POPEN",
        "agent_launch_method"         : "JSRUN",
        "task_launch_method"          : "JSRUN",
        "mpi_launch_method"           : "JSRUN",
        "pre_bootstrap_0"             : [
            "module load jsrun",
            "source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh"],
        "default_remote_workdir"      : "/p/gpfs1/$USER",
        "valid_roots"                 : ["/p/gpfs1/$USER",
                                         "$HOME"],
        "python_dist"                 : "anaconda",
        "virtenv"                     : "ve.rp",
        "virtenv_mode"                : "use",
        "rp_version"                  : "installed"
    }
}
```

### Test example
Executable:
```shell script
wget -q https://raw.githubusercontent.com/radical-cybertools/radical.pilot/devel/examples/hello_rp.sh
chmod +x hello_rp.sh
```
Script file `run_hello_rp.py` to run:
```python
#!/usr/bin/env python3

import radical.pilot as rp

N_TASKS = 10


if __name__ == '__main__':
    session = rp.Session()
    try:
        pmgr = rp.PilotManager(session=session)
        umgr = rp.UnitManager(session=session)
        pd_init = {'resource': 'llnl.lassen',
                   'runtime': 30,
                   'exit_on_error': True,
                   'project': 'cv19-a01',
                   'access_schema': 'local',
                   'cores': 40,
                   'input_staging': ['hello_rp.sh']}
        pdesc = rp.ComputePilotDescription(pd_init)
        pilot = pmgr.submit_pilots(pdesc)
        umgr.add_pilots(pilot)
        cuds = list()
        for _num in range(N_TASKS):
            cuds.append(rp.ComputeUnitDescription({
                'cpu_processes': 1,
                'cpu_process_type': 'MPI',
                'cpu_threads': 2,
                'cpu_thread_type': 'OpenMPI',
                'executable': './hello_rp.sh',
                'input_staging': [
                    {'source': 'pilot:///hello_rp.sh',
                     'target': 'unit:///hello_rp.sh',
                     'action': rp.LINK}],
                'output_staging': [
                    {'source': 'unit:///STDOUT',
                     'target': 'client:///output_hrp_%d.txt' % _num,
                     'action': rp.TRANSFER}]}))
        umgr.submit_units(cuds)
        umgr.wait_units()
    finally:
        session.close(download=True)
```

---

## Amber/AmberTools installation
- version 20
```shell script
# group workspace is used here:
#  /usr/workspace/cv_ddmd/ (personal dir: /usr/workspace/cv_ddmd/$USER/)

source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh
conda activate ve.rp

module load cuda/10.2.89

# get Amber20 -> provided by Arvind
# get AmberTools20 (based on the approach from WF3)
wget 'https://ambermd.org/cgi-bin/AmberTools20-get.pl?filename=AmberTools20.tar.bz2&Name=na&Institution=na&City=na&State=na&Country=na' -O AmberTools20.tar.bz2
tar xfj AmberTools20.tar.bz2
cd amber20_src/
ml gcc fftw
./configure -mpi -cuda -noX11 -nosse -nofftw3 gnu
make -j 40 install

# usage

source /usr/workspace/cv_ddmd/$USER/amber20_src/amber.sh
# export LD_LIBRARY_PATH="/usr/tce/packages/cuda/cuda-10.2.89/lib64:${LD_LIBRARY_PATH}"
```
- version 19 (following the approach from WF3)
```shell script
source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh
conda activate ve.rp

module load cuda/10.2.89
module load gcc/8.3.1

wget 'https://ambermd.org/cgi-bin/AmberTools19-get.pl?filename=AmberTools19.tar.bz2&Name=na&Institution=na&City=na&State=na&Country=na' -O AmberTools19.tar.bz2
tar xfj AmberTools19.tar.bz2
cd amber18/

# first part without CUDA
LANG=en_US.UTF-8 CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse gnu
make -j 40 install

# now CUDA part
./configure --with-python `which python` -nofftw3 --no-updates -cuda -nosse gnu
export LD_LIBRARY_PATH="/usr/tce/packages/cuda/cuda-10.2.89/lib64:${LD_LIBRARY_PATH}"
make -j 40 install

module load spectrum-mpi/rolling-release

# compile the -mpi version:
# first part without CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse -mpi gnu
make -j 40 install

# p.s. note that it is possible to also compile the combination of -mpi and -cuda. 
# It might be a good idea to have it too: with CUDA
CC=gcc CXX=g++ FC=gfortran ./configure --with-python `which python` -nofftw3 --no-updates -nosse -mpi -cuda gnu
make -j 40 install

# usage

source /p/gpfs1/$USER/amber18/amber.sh
```
## Pre-run | Set parameters

```shell script
source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh
conda activate ve.rp

cd /p/gpfs1/$USER
wget https://github.com/openbabel/openbabel/archive/openbabel-3-1-1.tar.gz
tar zxf openbabel-3-1-1.tar.gz
mkdir -p ./openbabel-openbabel-3-1-1/build ./openbabel
cd openbabel-openbabel-3-1-1/build
cmake ../ -DCMAKE_INSTALL_PREFIX=/p/gpfs1/$USER/openbabel
make -j 40 install
```
```shell script
export PATH=/p/gpfs1/$USER/openbabel/bin/:$PATH
```
```shell script
cd <WF2>/Parameters/
python paramterize.py
```

---

# Pre-run
```shell script
source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh
conda activate ve.rp

export AMBERHOME=/usr/workspace/cv_ddmd/$USER/amber20_src
# or export AMBERHOME=/p/gpfs1/$USER/amber18
```
**NOTE:** Edit file with credentials `creds_lassen.json`

---

## Additional information

[Resource Guide for New Livermore Computing Users](https://hpc.llnl.gov/training/tutorials/llnl-covid-19-hpc-resource-guide)

### Conda installers
`/collab/usr/gapps/python/blueos_3_ppc64le_ib_p9/conda/`

### Running jobs
https://computing.llnl.gov/tutorials/lc_resources/#RunningJobs

https://hpc.llnl.gov/training/tutorials/using-lcs-sierra-system#Running

### MyLC (dashboard)
https://lc.llnl.gov/lorenz/mylc/mylc.cgi
