Theta@ANL (for WF0)
===
- Deployment of RCT and its environment at Theta
- Setup and execute WF0 on Theta (launch execution script locally)
  - Preparation steps are followed by [setup instructions for Comet](https://github.com/2019-ncovgroup/DrugWorkflows/blob/devel/workflow-0/docs/setup_execute_comet.md)

# 1. Virtual environment deployment

## 1.1 Conda environment (basic)
```shell script
export PYTHONNOUSERSITE=True
export WF0_CONDA_ENV=ve.rp

module load miniconda-3
conda create -y -p $HOME/$WF0_CONDA_ENV --clone $CONDA_PREFIX
conda activate $HOME/$WF0_CONDA_ENV

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
# conda install -y cudatoolkit=10.1.243
conda update -y cudatoolkit
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

pip install radical.utils
pip install git+https://github.com/radical-cybertools/radical.saga.git@devel
pip install git+https://github.com/radical-cybertools/radical.pilot.git@project/cobalt
```

# 2. RCT related services

## 2.1. MongoDB installation (locally)
If MongoDB was already setup and initialized then just run the instance 
(see "Run MongoDB instance" subsection).
```shell script
cd $HOME
wget https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-suse15-4.4.0.tgz
tar -zxf mongodb-linux-x86_64-enterprise-suse15-4.4.0.tgz
mv mongodb-linux-x86_64-enterprise-suse15-4.4.0 mongo
mkdir -p mongo/data mongo/etc mongo/var/log mongo/var/run
touch mongo/var/log/mongodb.log
```

### Config setup
As [user guide](https://www.alcf.anl.gov/support-center/theta/mongodb) states 
_"Each server instance of MongoDB should have a unique port number, and this 
should be changed to a sensible number"_, then assigned port is
`59361`, which is a random number.
```shell script
cat > mongo/etc/mongodb.theta.conf <<EOT

processManagement:
  fork: true
  pidFilePath: $HOME/mongo/var/run/mongod.pid

storage:
  dbPath: $HOME/mongo/data

systemLog:
  destination: file
  path: $HOME/mongo/var/log/mongodb.log
  logAppend: true

net:
  bindIp: 0.0.0.0
  port: 59361
EOT
```

## 2.2. Run MongoDB instance
```shell script
# Launch the server
$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf
# Shutdown the server
$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf --shutdown  
```

## 2.3. MongoDB initialization
Initialize MongoDB (should be done ONLY once; if MongoDB instance was already 
running, then this step was completed)
```shell script
$HOME/mongo/bin/mongo --host `hostname -f` --port 59361
 > use rct_db
 > db.createUser({user: "rct", pwd: "jdWeRT634k", roles: ["readWrite"]})
 > exit
```

# 3. RP resource config for Theta
Corresponding resource config is already in the RP package 
([resource_anl](https://github.com/radical-cybertools/radical.pilot/blob/project/cobalt/src/radical/pilot/configs/resource_anl.json))

NOTE: default queue for tests is `debug-flat-quad`, production queue is 
`default` with minimum 128 nodes (WF0 has a special queue, see section 4.1 for 
details).

# 4. Run RCT-based workflows
Virtual environment activation
```shell script
module load miniconda-3
conda activate $HOME/ve.rp
```

Database URL
```shell script
export RADICAL_PILOT_DBURL="mongodb://rct:jdWeRT634k@`hostname -f`:59361/rct_db"
```

**OR** all pre-/post-execution actions (VE activation, start/stop DB) could be 
wrapped into an execution script (`rct_launcher.sh`):
```shell
#!/bin/sh

# - pre exec -
module load miniconda-3
conda activate $HOME/ve.rp

$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf

export RADICAL_PILOT_DBURL="mongodb://rct:jdWeRT634k@`hostname -f`:59361/rct_db"
export RADICAL_LOG_LVL=DEBUG
export RADICAL_PROFILE=TRUE

# - exec -
<workflow_launcher_script>

# - post exec -
$HOME/mongo/bin/mongod -f $HOME/mongo/etc/mongodb.theta.conf --shutdown
```

```shell
./rct_launcher.sh

### OR run it in background
# nohup ./rct_launcher.sh > OUTPUT 2>&1 </dev/null &
### check the status of the script running
# jobs -l
```

## 4.1. Run WF0 execution
Project name and corresponding queue are: `CVD-Mol-AI`, `CVD_Research` (backup
project is `CVD_Research`), and which are set in the configuration file 
`wf0.theta.cfg`.
