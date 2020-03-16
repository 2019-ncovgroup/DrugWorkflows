

| host     | max nodes | cpn | docks/node-hr | docks/corehr | docks/hr | total calls | notes   |
|----------|-----------|-----|---------------|--------------|----------|-------------|---------|
|    Theta |        128| 64  |         ~2.800|           45 | ~350.000 | 1.700.00 0  |         |
| Frontera |          4| 56  |        ~13.000|          230 |  ~50.000 | 1.500.00 0  | incompl |
|    Comet |           |     |               |              |          |             |         |
|    total |           |     |               |              |          | 4.400.00 0  |         |


 - docks / node-hr
   - docks           : `cat unit.000000/STDOUT | wc -l`
   - t_start         : `head -n 1 unit.000000/unit.000000.prof`
   - t_stop          : `tail -n 1 unit.000000/unit.000000.prof`
   - hours           : `(t_stop - t_start) / 3.600`
   - docs/nhr        : `docks / hours`
 - docks / core-hr   : `docks / node_hr / cpn`
 - total calls       : `cat rp.*/pilot.*/unit.*/STDOUT | wc -l`
 - total total calls : `cat results/*.out | wc -l`



