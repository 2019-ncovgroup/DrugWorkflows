`updated on: 05-18-2020`

# Lassen@LLNL

## Login ([docs](https://lc.llnl.gov/confluence/display/LC/SSH+Guide+for+Livermore+Computing))
```shell script
ssh -l <lcusername> lassen.llnl.gov
```
GPFS work directory: `/p/gpfs1/$USER` (IBM's Spectrum Scale file system)
Bank: `cv19-a01` ("shares")

## Environment installation
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
pip install git+https://github.com/radical-cybertools/radical.utils.git@devel
pip install git+https://github.com/radical-cybertools/radical.saga.git@devel
pip install git+https://github.com/radical-cybertools/radical.pilot.git@hotfix/lassen
pip install git+https://github.com/radical-cybertools/radical.entk.git@devel
```
ZMQ installation
```shell script
cd /p/gpfs1/$USER/

wget https://github.com/zeromq/libzmq/archive/v4.3.2.tar.gz
tar zxvf v4.3.2.tar.gz
cd libzmq-4.3.2/
./autogen.sh
./configure --prefix=`pwd -P`/install
make -j
make install
export LD_LIBRARY_PATH=`pwd -P`/install/lib:$LD_LIBRARY_PATH
export LD_RUN_PATH=`pwd -P`/install/lib:$LD_RUN_PATH
pip install --no-cache-dir --force-reinstall --ignore-installed --no-binary :all: --install-option="--zmq=`pwd -P`/install" pyzmq
```
```shell script
(ve.rp) [:libzmq-4.3.2]$ ldd /p/gpfs1/$USER/.miniconda3/envs/ve.rp/lib/python3.7/site-packages/zmq/backend/cython/socket.cpython-37m-powerpc64le-linux-gnu.so | grep zmq
	libzmq.so.5 => /p/gpfs1/$USER/libzmq-4.3.2/install/lib/libzmq.so.5 (0x00002000000c0000)
```

## RADICAL-Pilot setup
User config dir: `mkdir -p $HOME/.radical/pilot/configs/`

Resource config file: `$HOME/.radical/pilot/configs/resource_llnl.json`:
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

Pre-run
```shell script
source /p/gpfs1/$USER/.miniconda3/etc/profile.d/conda.sh
conda activate ve.rp
```

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
