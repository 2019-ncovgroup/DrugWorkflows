#!/usr/bin/env python3

import os
import sys

import radical.pilot as rp
import radical.utils as ru


def link(src, tgt):
    out, err, ret = ru.sh_callout('ln -s %s %s' % (src, tgt))
    assert(not ret), [out, err]


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    target     =     sys.argv[1]   # 'localhost'
    dbase      =     sys.argv[2]   # 'adpr_ena_db'
    nodes      = int(sys.argv[3])  # 3

    master  = '%s/wf1_master.py' % os.path.abspath(os.getcwd())
    worker  = '%s/wf1_worker.py' % os.path.abspath(os.getcwd())

    cfg        = ru.read_json('config.json')[target]
    model      = '%s/../../Model-generation' % os.getcwd()
    cpn        = cfg['cpn']
    gpn        = cfg['gpn']

    n_workers  = nodes * gpn

    session    = rp.Session()
    try:

        pmgr   = rp.PilotManager(session=session)
        umgr   = rp.UnitManager(session=session)
        pdinit = cfg['pilot']

        pdinit["cores"]        += nodes * cpn
     #  pdinit["gpus"]          = nodes * gpn
        pdinit["exit_on_error"] = True
        pdinit["input_staging"] = [model,
                                   'wf1_master.py',
                                   'wf1_worker.py',
                                   'wf1_worker.sh',
                                   'oe_license.txt',
                                   'config.json'
                                  ]

        pdescs = rp.ComputePilotDescription(pdinit)
        pilots = pmgr.submit_pilots(pdescs)

        umgr.add_pilots(pilots)
        cuds  = list()
        for i in range(1):

            udinit = cfg['master']
            udinit['cpu_processes'] = 1
            udinit['executable']    =  '$PWD/wf1_master.py'
            udinit['arguments']     =  [dbase, n_workers, target]
            udinit['input_staging'] = [{'source': 'pilot:///Model-generation/input',
                                        'target': 'unit:///input',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///config.json',
                                        'target': 'unit:///config.json',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///Model-generation/impress_md',
                                        'target': 'unit:///impress_md',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///oe_license.txt',
                                        'target': 'unit:///oe_license.txt',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_master.py',
                                        'target': 'unit:///wf1_master.py',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_worker.py',
                                        'target': 'unit:///wf1_worker.py',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_worker.sh',
                                        'target': 'unit:///wf1_worker.sh',
                                        'action': rp.LINK},
                                      ]
            cud = rp.ComputeUnitDescription(udinit)
            cuds.append(cud)

        umgr.submit_units(cuds)
        umgr.wait_units()

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------

