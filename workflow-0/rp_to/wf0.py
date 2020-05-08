#!/usr/bin/env python3

import os
import sys
import glob

import radical.utils as ru
import radical.pilot as rp


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    cfg_file  = sys.argv[1]
    rec_file  = sys.argv[2]
    smiles    = sys.argv[3]

    session   = None

    assert(smiles.endswith('.csv'))

    try:

        cfg       = ru.Config(cfg=ru.read_json(cfg_file))
        rec_path  = 'input/receptorsV5.1/'
        receptors = list()

        with open(rec_file, 'r') as fin:
            for line in fin.readlines():
                line  = line.strip()
                elems = line.split()
                if elems[0] != '#':
                    assert(os.path.isfile('%s/%s.oeb' % (rec_path, elems[0])))
                    receptors.append(elems[0])

        session = rp.Session()
        pmgr    = rp.PilotManager(session=session)
        umgr    = rp.UnitManager(session=session)

        for receptor in receptors:

            print('=== %s' % receptor)

            cfg.workload.receptor = '%s.oeb' % receptor
            cfg.workload.smiles   = smiles
            cfg.workload.name     = '%s_-_%s' % (receptor, smiles[:-4])

            ru.write_json(cfg, 'wf0.%s.cfg' % receptor)

            nodes     = cfg.nodes
            cpn       = cfg.cpn
            gpn       = cfg.gpn
            n_masters = cfg.n_masters
            workload  = cfg.workload

            pd = rp.ComputePilotDescription(cfg.pilot_descr)
            pd.cores   = nodes * cpn
            pd.gpus    = nodes * gpn
            pd.runtime = cfg.runtime

            pilot = pmgr.submit_pilots(pd)
            pid   = pilot.uid

            umgr.add_pilots(pilot)

            tds = list()

            for i in range(n_masters):
                td = rp.ComputeUnitDescription(cfg.master_descr)
                td.executable     = "python3"
                td.arguments      = ['wf0_master.py', i]
                td.cpu_threads    = 1
                td.pilot          = pid
                td.input_staging  = [{'source': cfg.master,
                                      'target': 'wf0_master.py',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': cfg.worker,
                                      'target': 'wf0_worker.py',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': 'wf0.%s.cfg' % receptor,
                                      'target': 'wf0.cfg',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': workload.input_dir,
                                      'target': 'input_dir',
                                      'action': rp.LINK,
                                      'flags' : rp.DEFAULT_FLAGS}
                                    ]
              # td.output_staging = [{'source': '%s.sdf'      % (workload.name),
              #                       'target': '%s.%02d.sdf' % (workload.name, i),
              #                       'action': rp.TRANSFER,
              #                       'flags' : rp.DEFAULT_FLAGS}]
                tds.append(td)

            task = umgr.submit_units(tds)

        # all pilots and masters submittet - wait for all to finish
        umgr.wait_units()
    finally:
        if session: 
            session.close(download=True)


# ------------------------------------------------------------------------------

