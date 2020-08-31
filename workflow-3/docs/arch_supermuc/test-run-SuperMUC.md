`updated on: 05-04-2020`

# SuperMUC-NG
`export CV_CONDA_ENV=ve.rp`

## General description of environment setup
https://github.com/2019-ncovgroup/DrugWorkflows/blob/devel/conda-SuperMUC.txt

---

## Run MongoDB
Dedicated node for MongoDB (connect to it from the login node)
```shell script
ssh 172.16.224.152

source ~/$CV_CONDA_ENV/bin/activate
mongod --fork --dbpath ~/mongodb --logpath ~/mongodb/log --bind_ip 127.0.0.1,172.16.224.152 --port 27017
```

\* **Note**: stop mongod service
```shell script
ps aux | grep mongod | grep -v grep | cut -c 10-16 | xargs kill
rm ~/mongodb/mongod.lock
```

---

## Run RP
**SSH to login node**

Resource config file `<path>/.radical/pilot/configs/resource_lrz.json`:
```shell script
{
    "supermuc-ng": {
        "description"                 : "",
        "notes"                       : "",
        "schemas"                     : ["local"],
        "local"                       :
        {
            "job_manager_endpoint"    : "slurm://localhost/",
            "filesystem_endpoint"     : "file://localhost/"
        },
        "cores_per_node"              : 48,
        "default_queue"               : "test",
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
        "virtenv"                     : "$HOME/ve.rp",
        "virtenv_mode"                : "use",
        "rp_version"                  : "installed"
    }
}
```

### Test example
Executable:
```shell script
wget https://raw.githubusercontent.com/radical-cybertools/radical.pilot/devel/examples/hello_rp.sh
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
        pd_init = {'resource': 'lrz.supermuc-ng',
                   'runtime': 60,
                   'exit_on_error': True,
                   'project': 'pn98ve',
                   'queue': 'general',
                   'access_schema': 'local',
                   'cores': 20,
                   'input_staging': ['hello_rp.sh']}
        pdesc = rp.ComputePilotDescription(pd_init)
        pilot = pmgr.submit_pilots(pdesc)
        umgr.add_pilots(pilot)
        cuds = list()
        for _num in range(N_TASKS):
            cuds.append(rp.ComputeUnitDescription({
                'cpu_processes': 1,
                'cpu_process_type': rp.MPI,
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

Pre-run:
```shell script
# environment variable(s)
export RADICAL_PILOT_DBURL="mongodb://rct:rct_test@172.16.224.152/rct_test"

source ~/$CV_CONDA_ENV/bin/activate
```
