#!/usr/bin/env python3

import os
import sys

import radical.utils as ru
import radical.pilot as rp


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    cfg_file  = sys.argv[1]
    receptor  = sys.argv[2]
    smiles    = sys.argv[3]

    cfg       = ru.Config(cfg=ru.read_json(cfg_file))

    assert(receptor.endswith('.oeb'))   # strip '.oeb' 
    assert(smiles.endswith('.csv'))     # strip '.csv' 

    cfg.workload.receptor = receptor
    cfg.workload.smiles   = smiles
    cfg.workload.name     = '%s_-_%s' % (receptor[:-4], smiles[:-4])

    assert(not os.path.exists('%s.sdf' % cfg.workload.name))

    ru.write_json(cfg, 'wf0.cfg')

    nodes     = cfg.nodes
    cpn       = cfg.cpn
    gpn       = cfg.gpn
    n_masters = cfg.n_masters
    workload  = cfg.workload
    session   = rp.Session()
    try:
        pd = rp.ComputePilotDescription(cfg.pilot_descr)
        pd.cores   = nodes * cpn
        pd.gpus    = nodes * gpn
        pd.runtime = cfg.runtime

        tds = list()

        for i in range(n_masters):
            td = rp.ComputeUnitDescription(cfg.master_descr)
            td.executable     = "python3"
            td.arguments      = ['wf0_master.py', i]
            td.cpu_threads    = 1
            td.input_staging  = [{'source': cfg.master,
                                  'target': 'wf0_master.py',
                                  'action': rp.TRANSFER,
                                  'flags' : rp.DEFAULT_FLAGS},
                                 {'source': cfg.worker,
                                  'target': 'wf0_worker.py',
                                  'action': rp.TRANSFER,
                                  'flags' : rp.DEFAULT_FLAGS},
                                 {'source': 'wf0.cfg',
                                  'target': 'wf0.cfg',
                                  'action': rp.TRANSFER,
                                  'flags' : rp.DEFAULT_FLAGS},
                                 {'source': workload.input_dir,
                                  'target': 'input_dir',
                                  'action': rp.LINK,
                                  'flags' : rp.DEFAULT_FLAGS}
                                ]
            td.output_staging = [{'source': '%s.sdf'      % (workload.name),
                                  'target': '%s.%02d.sdf' % (workload.name, i),
                                  'action': rp.TRANSFER,
                                  'flags' : rp.DEFAULT_FLAGS}]
            tds.append(td)

        pmgr  = rp.PilotManager(session=session)
        umgr  = rp.UnitManager(session=session)
        pilot = pmgr.submit_pilots(pd)
        task  = umgr.submit_units(tds)

        umgr.add_pilots(pilot)
        umgr.wait_units()

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------

