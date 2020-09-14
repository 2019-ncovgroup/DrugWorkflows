`updated on: 09-10-2020`

SuperMUC-NG@LRZ
===
Package (archive file) with corresponding environment should be prepared
outside of SuperMUC-NG, and then by using `conda-pack` be transferred there.

# 1. Virtual environment deployment
Conda package preparation is done at the RADICAL machine (jetstream VM), since 
its IP address is approved for ssh-connection to SuperMUC-NG.

## 1.1. Conda environment (basic)
```shell script
export PYTHONNOUSERSITE=True
export CVD_CONDA_ENV=ve.rp
export CVD_BASE_DIR=/hppfs/work/pn98ve/common

export PREFIX=$HOME
mkdir -p $PREFIX
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $PREFIX/miniconda.sh
chmod +x $PREFIX/miniconda.sh
$PREFIX/miniconda.sh -b -p $PREFIX/.miniconda3
source $PREFIX/.miniconda3/bin/activate
conda update -y -n base -c defaults conda
conda create -y -n $CVD_CONDA_ENV python=3.7
conda activate $CVD_CONDA_ENV

conda config --add channels conda-forge
conda update -y --all
```

## 1.2. Special packages
NOTE: below is the set of packages for the current installation, if the
particular workflow requires other set of packages, then this section should 
be updated.
```shell script
conda config --add channels omnia-dev/label/cuda101 \
             --add channels omnia/label/cuda101
conda install -y cudatoolkit=10.1.243
conda install -y atomicwrites attrs blas fftw3f importlib_metadata libtiff \
                 more-itertools ninja olefile packaging pillow pluggy py \
                 pytest pandas psutil docopt pymbar openmm
conda install -y -c openeye openeye-toolkits
```

## 1.3. RADICAL-Cybertools (RCT) installation
```shell script
conda install -y apache-libcloud chardet colorama future idna msgpack-python \
                 netifaces ntplib parse pymongo python-hostlist pyzmq regex \
                 requests setproctitle urllib3

pip install git+https://github.com/radical-cybertools/radical.utils.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.saga.git@project/covid-19
pip install git+https://github.com/radical-cybertools/radical.pilot.git@project/covid-19

# if needed for the corresponding workflow
pip install git+https://github.com/radical-cybertools/radical.entk.git@devel
```

## 1.4. Pack the environment with `conda-pack`
Pack conda environment, and move it to and set it up on SuperMUC-NG (should be 
used the RADICAL machine, since its IP is approved to be connected from)
```shell script
conda install -y conda-pack 
conda pack -n $CVD_CONDA_ENV
scp $CVD_CONDA_ENV.tar.gz <user_id>@skx.supermuc.lrz.de:$CVD_BASE_DIR
```

## 1.5. Deployment at SuperMUC-NG
NOTE: work directory for every user of the project `pn98ve` at SuperMUC-NG is
in the environment variable `$WORK_pn98ve`; common work directory for the
project is `/hppfs/work/pn98ve/common`
```shell script
# connect from the RADICAL machine (jetstream VM)
ssh <user_id>@skx.supermuc.lrz.de
export CVD_CONDA_ENV=ve.rp
export CVD_BASE_DIR=/hppfs/work/pn98ve/common
export PATH=$CVD_BASE_DIR/$CVD_CONDA_ENV/bin:$PATH

mkdir -p $CVD_BASE_DIR/$CVD_CONDA_ENV
cd $CVD_BASE_DIR
tar -xzf $CVD_CONDA_ENV.tar.gz -C $CVD_CONDA_ENV/
source $CVD_CONDA_ENV/bin/activate
conda-unpack
```

# 2. RCT related services at SuperMUC-NG
Check that RCT related services are running (inside the batch job), that
includes MongoDB and RabbitMQ.
```shell script
module load slurm_setup
squeue --name rct_services
# example:
#      JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
#     800276      tmp3 rct_serv  di67rok  R       0:12      1 i01r03c01s12
```
If there is no such batch job, then run it from the predefined batch script.
```shell script
module load slurm_setup
sbatch /hppfs/work/pn98ve/common/rct_services.slurm
```
If there is no a predefined script, then follow the next steps to create and
run it (`rct_services.slurm`).

## 2.1. Batch script for RCT related services
__THIS STEP SHOULD BE SKIPPED IF THE CORRESPONDING SCRIPT EXISTS__

__MongoDB__. Current MongoDB directory is `$CVD_BASE_DIR/workdir_mongod`, 
which is a copy of the original one: `$CVD_BASE_DIR/mongo-4.4.0`. Firstly
need to update/confirm `$CVD_BASE_DIR/workdir_mongod/etc/mongod.conf` to
have `bindIpAll: true`.

__RabbitMQ__. Corresponding modules (`erlang` and `rabbitmq`) are located at 
`$CVD_BASE_DIR/spack/modules/x86_64/linux-sles12-x86_64`. Current RabbitMQ
directory is `$CVD_BASE_DIR/workdir_rabbitmq`, which is a copy of the original 
one: `$CVD_BASE_DIR/rabbitmq_server-3.8.7`. Service uses default port `5672`.

Config file for RabbitMQ
```shell script
cd $CVD_BASE_DIR
cat > workdir_rabbitmq/etc/rabbitmq/rabbitmq.conf <<EOT
## Networking
## ====================
loopback_users.guest = false
## ====================
EOT
```

Next step is to create a batch script:
```shell script
cd $CVD_BASE_DIR
cat > rct_services.slurm <<EOT
#!/bin/bash

#SBATCH --account=pn98ve
#SBATCH --partition=tmp3
#SBATCH --time=00:00:00
#SBATCH --qos=nolimit
#SBATCH -J "rct_services"
#SBATCH -D /hppfs/work/pn98ve/common/rct_services
#SBATCH -o rct_services.out
#SBATCH -e rct_services.err

module load slurm_setup
export CVD_BASE_DIR=/hppfs/work/pn98ve/common

# save host name
echo "$(hostname -s)opa" > $CVD_BASE_DIR/rct_services/HOSTNAME

# run mongodb
$CVD_BASE_DIR/workdir_mongod/usr/bin/mongod --config $CVD_BASE_DIR/workdir_mongod/etc/mongod.conf

# run rabbitmq
module use $CVD_BASE_DIR/spack/modules/x86_64/linux-sles12-x86_64
module load erlang
module load rabbitmq
export RABBITMQ_BASE=$CVD_BASE_DIR/workdir_rabbitmq
export RABBITMQ_CONFIG_FILE=$RABBITMQ_BASE/etc/rabbitmq/rabbitmq.conf
$RABBITMQ_BASE/sbin/rabbitmq-server -detached

while true; do sleep 1000; done
EOT

module load slurm_setup
sbatch rct_services.slurm
```

#### Name of the host running RCT related services
File `/hppfs/work/pn98ve/common/rct_services/HOSTNAME` contains the hostname.

## 2.2. MongoDB initialization
Initialize MongoDB (should be done ONLY once; if MongoDB instance was already
running, then this step was completed)
```shell script
mongo --host "$(cat /hppfs/work/pn98ve/common/rct_services/HOSTNAME)"
 > use rct_db
 > db.createUser({user: "rct", pwd: "jdWeRT634k", roles: ["readWrite"]})
 > exit
```

# 3. RP resource config for SuperMUC-NG
Use one of the following locations to keep the configuration data:
`$HOME/.radical/pilot/configs/resource_lrz.json` (user space) OR
`$CVD_BASE_DIR/$CVD_CONDA_ENV/lib/python3.7/site-packages/radical/pilot/configs/resource_lrz.json` 
(virtenv space)

NOTE: Parameters that might be workflow-specific are: `"virtenv"` and 
`"pre_bootstrap_0"` (update them accordingly if needed).
```json
{
    "supermuc-ng": {
        "description"                 : "",
        "notes"                       : "Access only from registered IP addresses",
        "schemas"                     : ["local", "ssh"],
        "ssh"                         :
        {
            "job_manager_endpoint"    : "slurm+ssh://skx.supermuc.lrz.de/",
            "filesystem_endpoint"     : "sftp://skx.supermuc.lrz.de/"
        },
        "local"                       :
        {
            "job_manager_endpoint"    : "slurm://localhost/",
            "filesystem_endpoint"     : "file://localhost/"
        },
        "cores_per_node"              : 48,
        "default_queue"               : "tmp3",
        "resource_manager"            : "SLURM",
        "agent_scheduler"             : "CONTINUOUS",
        "agent_spawner"               : "POPEN",
        "agent_launch_method"         : "SRUN",
        "task_launch_method"          : "SRUN",
        "mpi_launch_method"           : "SRUN",
        "pre_bootstrap_0"             : ["module load slurm_setup"],
        "default_remote_workdir"      : "$HOME",
        "valid_roots"                 : ["$HOME",
                                         "$SCRATCH"],
        "python_dist"                 : "anaconda",
        "virtenv"                     : "/hppfs/work/pn98ve/common/ve.rp",
        "virtenv_mode"                : "use",
        "rp_version"                  : "installed"
    }
}
```

# 4. Run RCT-based workflows
Activate virtual environment
```shell script
export CVD_CONDA_ENV=ve.rp
export CVD_BASE_DIR=/hppfs/work/pn98ve/common

cd $CVD_BASE_DIR
source $CVD_CONDA_ENV/bin/activate
```

Database URL
```shell script
export RADICAL_PILOT_DBURL="mongodb://rct:jdWeRT634k@$(cat /hppfs/work/pn98ve/common/rct_services/HOSTNAME)/rct_db"

```
RabbitMQ settings
```shell script
export RMQ_HOSTNAME="$(cat /hppfs/work/pn98ve/common/rct_services/HOSTNAME)"
export RMQ_PORT=5672
```

## 4.1. Open Babel package (optional)
```shell script
module use $WORK_pn98ve/../common/spack/modules/x86_64/linux-sles12-x86_64
module load openbabel/3.0.0
```

## 4.2. NAMD package (optional)
```shell script
module use $WORK_pn98ve/../common/spack/modules/skylake/linux-sles12-skylake_avx512
module load namd/2.14-impi
# OR
# module load namd/2.14-impi-smp
```

