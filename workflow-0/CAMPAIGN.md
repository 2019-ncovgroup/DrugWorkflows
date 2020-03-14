# Workflow-0 Campaign

## Targets

Downloaded from https://anl.app.box.com/s/m9aw6c7lfv6kv2eshgoaj6jphtc8vyz1

| OEB                             | Machine  | Assignee | State   | Missing |
|---------------------------------|----------|----------|---------|---------|
| Nsp10_pocket1_receptor.oeb      | Theta    | AM       | Done    |   1.6 % |
| Nsp10_pocket3_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| Nsp10_pocket26_receptor.oeb     | Comet    | MT       | Done    |   0.1 % |
|---------------------------------|----------|----------|---------|---------|
| ADRP_pocket1_receptor.oeb       | Comet    | MT       | Done    |   0.1 % |
| ADRP_pocket12_receptor.oeb      | Comet    | MT       | Done    |         |
| ADRP_pocket13_receptor.oeb      | Comet    | MT       | Partial |  28.4 % |
|---------------------------------|----------|----------|---------|---------|
| nsp15-CIT_pocket1_receptor.oeb  | Theta    | AM       | Done    |   7.6 % |
| nsp15-CIT_pocket6_receptor.oeb  | Theta    | AM       | Done    |   4.3 % |
| nsp15-CIT_pocket13_receptor.oeb | Theta    | AM       | Partial |  69.1 % |
| nsp15-CIT_pocket18_receptor.oeb | Theta    | MT       | Done    |         |
| nsp15-CIT_pocket37_receptor.oeb | Frontera | IP       |         |         |
|---------------------------------|----------|----------|---------|---------|
| PLPro_pocket3_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| PLPro_pocket4_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| PLPro_pocket6_receptor.oeb      | Frontera | MT       | Done    |         |
| PLPro_pocket23_receptor.oeb     | Theta    | AM       |         |         |
|---------------------------------|----------|----------|---------|---------|
| CoV_pocket1_receptor.oeb        | Frontera | AM       | Done    |   4.4 % |
| CoV_pocket2_receptor.oeb        | Frontera | AM       | Done    |   5.4 % |
| CoV_pocket8_receptor.oeb        | Theta    | AM       | Done    |   3.9 % |
| CoV_pocket10_receptor.oeb       | Frontera | AM       | Partial |  67.9 % |


## Runs

| Run | command                    | machine  | SMILES               | OEB                              |
|-----|----------------------------|----------|----------------------|----------------------------------|
| 1   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | Nsp10_pocket26_receptor.oeb      |
| 2   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | Nsp10_pocket26_receptor.oeb      |
| 3   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | ADRP_pocket1_receptor.oeb        |
| 4   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | ADRP_pocket1_receptor.oeb        |
| 5   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | ADRP_pocket13_receptor.oeb       |
| 6   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | Nsp10_pocket3_receptor.oeb       |
| 7   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket3_receptor.oeb       |
| 8   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket4_receptor.oeb       |
| 9   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket6_receptor.oeb       |
| 10  | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket6_receptor.oeb       |
| 11  | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket3_receptor.oeb       |
| 12  | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket4_receptor.oeb       |
| 13  | theta_dock_rp_loop.py      | Theta    | discovery_set_db.smi | nsp15-CIT_pocket18_receptor.oeb  |


## Data

| Run | SID                                                               | Idx    | # pilots | task/pilot | # Idx  |
|-----|-------------------------------------------------------------------|--------|----------|------------|--------|
| 1   | rp.session.two.mturilli.018334.0022                               | 0      | 2        | 50         | 2000   |
| 2   | rp.session.two.mturilli.018334.0023                               | 200000 | 2        | 50         | 2000   |
| 3   | rp.session.two.mturilli.018334.0024                               | 0      | 2        | 50         | 2000   |
| 4   | rp.session.two.mturilli.018334.0025                               | 200000 | 2        | 50         | 2000   |
| 5   | rp.session.login3.frontera.tacc.utexas.edu.mturilli.018335.0000\* | 0      | 1        | 4          | 80000  |
| 6   | rp.session.login2.frontera.tacc.utexas.edu.tg853783.018335.0000\* | 0      | 1        | 4          | 80000  |
| 7   | rp.session.login4.frontera.tacc.utexas.edu.tg864504.018335.0000   | 0      | 1        | 4          | 40000  |
| 8   | rp.session.login3.frontera.tacc.utexas.edu.mturilli.018335.0003   | 0      | 1        | 4          | 40000  |
| 9   | rp.session.login2.frontera.tacc.utexas.edu.tg853783.018335.0001   | 0      | 1        | 4          | 40000  |
| 10  | rp.session.login2.frontera.tacc.utexas.edu.tg853783.018335.0002   | 160000 | 1        | 4          | 40000  |
| 11  | rp.session.login4.frontera.tacc.utexas.edu.tg864504.018335.0001   | 160000 | 1        | 4          | 40000  |
| 12  | rp.session.login3.frontera.tacc.utexas.edu.mturilli.018335.0004   | 160000 | 1        | 4          | 40000  |
| 13  | rp.session.thetalogin5.mturilli.018335.0005                       | 0      | 1        | 128        | 2500   |

* \* Partial, killed early by end of walltime
