# Workflow-0 Campaign

## Targets 

Downloaded from https://anl.app.box.com/s/m9aw6c7lfv6kv2eshgoaj6jphtc8vyz1

| OEB                             | Machine  | Assignee | State |
|---------------------------------|----------|----------|-------|
| Nsp10_pocket1_receptor.oeb      | Theta    | AM       | Done  |
| Nsp10_pocket3_receptor.oeb      | Frontera | MT       |       |
| Nsp10_pocket26_receptor.oeb     | Comet    | MT       | Done  |
|---------------------------------|----------|----------|-------|
| ADRP_pocket1_receptor.oeb       | Comet    | MT       | Done  |
| ADRP_pocket12_receptor.oeb      | Comet    | MT       | Done  |
| ADRP_pocket13_receptor.oeb      | Comet    | MT       |       | 
|---------------------------------|----------|----------|-------|
| nsp15-CIT_pocket1_receptor.oeb  |          |          |       |
| nsp15-CIT_pocket6_receptor.oeb  |          |          |       |
| nsp15-CIT_pocket13_receptor.oeb |          |          |       |
| nsp15-CIT_pocket18_receptor.oeb |          |          |       |
| nsp15-CIT_pocket37_receptor.oeb |          |          |       |
|---------------------------------|----------|----------|-------|
| PLPro_pocket3_receptor.oeb      | Frontera | MT       |       |
| PLPro_pocket4_receptor.oeb      | Frontera | MT       |       |
| PLPro_pocket6_receptor.oeb      | Frontera | MT       |       |
| PLPro_pocket23_receptor.oeb     |          |          |       |
|---------------------------------|----------|----------|-------|
| CoV_pocket1_receptor.oeb        | Frontera | AM       | Done  |
| CoV_pocket2_receptor.oeb        | Frontera | AM       |       |
| CoV_pocket8_receptor.oeb        | Theta    | AM       |       |
| CoV_pocket10_receptor.oeb       | Frontera | AM       |       |


## Runs

| Run | command                    | machine  | SMILES               | OEB                         |
|-----|----------------------------|----------|----------------------|-----------------------------|
| 1   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | Nsp10_pocket26_receptor.oeb |
| 2   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | Nsp10_pocket26_receptor.oeb |
| 3   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | ADRP_pocket1_receptor.oeb   |
| 4   | theta_dock_rp_loop.py      | comet    | discovery_set_db.smi | ADRP_pocket1_receptor.oeb   |
| 5   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | ADRP_pocket13_receptor.oeb  |
| 6   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | Nsp10_pocket3_receptor.oeb  |
| 7   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket3_receptor.oeb  |
| 8   | theta_dock_rp_loop.py      | Frontera | discovery_set_db.smi | PLPro_pocket4_receptor.oeb  |

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

* \* Partial, killed early by end of walltime
