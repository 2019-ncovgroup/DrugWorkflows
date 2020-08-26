# Setup and Execute W0 on Comet from the RADICAL JetStream VM

## Setup on Comet
```
ssh w0comet@129.114.17.185
myproxy-logon -s myproxy.xsede.org -l user_name -t 72
gsissh comet.sdsc.xsede.org
```

1. Edit RP resource configuration file and push it to the `project/covid-19` branch: <https://github.com/radical-cybertools/radical.pilot/blob/project/covid-19/src/radical/pilot/configs/resource_xsede.json#L405>
1. Edit workflow0 configuration file and push it to the `devel` branch of the `DrugWorkflows` repo under `/workflow-0/wf0_oe_<anme_of_resource>/wf0.<name_of_resource.cfg `: <https://github.com/2019-ncovgroup/DrugWorkflows/blob/devel/workflow-0/wf0_oe_comet/wf0.comet.cfg>. NOTE: 
    * `$HOME` is not expanded when used in JSON. Change `/home/mturilli` with your home path on Comet.
    * Add timeout (define where once the cleanup has been done)
1. Comment out <https://github.com/2019-ncovgroup/DrugWorkflows/blob/devel/workflow-0/wf0_oe_frontera/wf0.py#L154>
1. Copy OpenEye license from Frontera to Comet:
   ```
   cd ~/DrugWorfklows/workflow-0/
   scp -r mturilli@frontera.tacc.utexas.edu:/scratch1/07305/rpilot/merzky/tg803521/covid-19-0/DrugWorfklows/workflow-0/oe_license.txt .
   ```
1. Copy relevant receptors from Frontera to Comet: 
   ```
   cd ~/Model-generation/input
   scp -r mturilli@frontera.tacc.utexas.edu:/scratch1/07305/rpilot/merzky/tg803521/covid-19-0/Model-generation/input/receptors.v7 .
   ```
1. Copy relevant smile files from Frontera to Comet: 
   ```
   cd ~/Model-generation/input
   scp -r mturilli@frontera.tacc.utexas.edu:/scratch1/07305/rpilot/merzky/tg803521/covid-19-0/Model-generation/input/Orderable_zinc_db_enaHLL.csv .`
   ```
1. Link input:
   ```
   ln -s /home/mturilli/Model-generation/input input
   ```

Note:

* The resource configuration file uses a static VE. 
* 1 worker per compute node: the mpi method determines the number of workers we can run concurrently.

## Setup on 

1. Edit `/home/w0comet/DrugWorfklows/workflow-0/wf0_oe_comet/wf0.py`, L110:
   ```
   110         #d    = rs.filesystem.Directory('ssh://frontera/scratch1/07305/rpilot/workflow-0-results')
   111         d    = rs.filesystem.Directory('gsissh://comet/workflow-0-results')
   ```
1. Copy receptors from Comet and link them:
   ```
   myproxy-logon -s myproxy.xsede.org -l <user_name> -t 72
   cd /home/w0comet/Model-generation/input/
   gsiscp -r comet.sdsc.xsede.org:Model-generation/input/receptors.v7 .
   gsiscp -r comet.sdsc.xsede.org:Model-generation/input/Orderable_zinc_db_enaHLL.csv .
   cd /home/w0comet/DrugWorfklows/workflow-0/wf0_oe_comet/
   ln -s ~/Model-generation/input input
   ```

## Execute

```
tmux new -s wf0_comet
cd DrugWorfklows/workflow-0/wf0_oe_comet
. setup.sh.shadow
vi receptors.dat
./wf0.py wf0.comet.cfg receptors.dat
```

