#!/usr/bin/env python3

import os
import sys
import pandas as pd

import radical.pilot as rp
import radical.utils as ru


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':


    target     =     sys.argv[1]
    smi_fname  =     sys.argv[2]
    tgt_fname  =     sys.argv[3]
    idx_start  = int(sys.argv[4])
    chunk_size = int(sys.argv[5])
    n_chunks   = int(sys.argv[6])

    n_pilots   = n_chunks  # NOTE

    cfg        = ru.read_json('config.json')
    model      = cfg[target]['model']
    conda      = cfg[target]['conda']

    smiles     = pd.read_csv('%s/%s' % (model, smi_fname), sep=' ', header=None)
    n_smiles   = smiles.shape[0]

    idx        = idx_start
    session    = rp.Session()
    try:
        pmgr   = rp.PilotManager(session=session)
        umgr   = rp.UnitManager(session=session)
        pdinit = cfg[target]['pilot']

        pdinit["exit_on_error"] = True,
        pdinit["input_staging"] = [model]

        pdescs = [rp.ComputePilotDescription(pdinit) for i in range(n_pilots)]
        pilots = pmgr.submit_pilots(pdescs)

        umgr.add_pilots(pilots)

        for p in range(n_pilots):

            cuds = list()

            for i in range(chunk_size):

                task_size = 1  # NOTE: NOT FLEXIBLE

                idx = idx_start + p * chunk_size + i
              # print(p, i, idx)

                cud = rp.ComputeUnitDescription()
                cud.cpu_processes  = 1
                cud.executable     = './theta_dock.sh'
                cud.arguments      =  [smi_fname, tgt_fname, idx, task_size]
                cud.pre_exec       =  ['. %s/etc/profile.d/conda.sh' % conda,
                                       'conda activate covid-19-0']
                cud.environment    =  {'OE_LICENSE': 'oe_license.txt'}
                cud.input_staging  = [{'source': 'pilot:///Model-generation/input',
                                       'target': 'unit:///input',
                                       'action': rp.LINK},
                                      {'source': 'pilot:///Model-generation/impress_md',
                                       'target': 'unit:///impress_md',
                                       'action': rp.LINK},
                                      {'source': 'pilot:///Model-generation/oe_license.txt',
                                       'target': 'unit:///oe_license.txt',
                                       'action': rp.LINK},
                                      {'source': 'pilot:///Model-generation/theta_dock.sh',
                                       'target': 'unit:///theta_dock.sh',
                                       'action': rp.LINK},
                                      {'source': 'pilot:///Model-generation/theta_dock.py',
                                       'target': 'unit:///theta_dock.py',
                                       'action': rp.LINK},
                                      ]
                cud.output_staging = [{'source': 'unit:///STDOUT',
                                       'target': 'client:///output/output.%d' % idx,
                                       'action': rp.TRANSFER}]
                cuds.append(cud)

            # chunk defined for pilot
            print('submit %d tasks as chunk %d' % (len(cuds), p))
            umgr.submit_units(cuds)

        # all chunks submitted to pilots
        print('wait all')
        umgr.wait_units()

    finally:
      # session.close(download=True)
        pass


# ------------------------------------------------------------------------------

