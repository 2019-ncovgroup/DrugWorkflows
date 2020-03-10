#!/usr/bin/env python3

import os
import sys
import pandas as pd

import radical.pilot as rp


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    smi_fname  = sys.argv[1]
    tgt_fname  = sys.argv[2]
    path       = '/home/merzky/projects/covid/Model-generation/'
    conda      = '/home/merzky/.miniconda3/'

    smiles     = pd.read_csv('%s/%s' % (path, smi_fname), sep=' ', header=None)
    n_smiles   = smiles.shape[0]
    chunk_size = 10
    session    = rp.Session()

    try:
        pmgr   = rp.PilotManager(session=session)
        umgr   = rp.UnitManager(session=session)
        pd_init = {'resource'      : 'local.localhost',
                   'runtime'       : 30,
                   'exit_on_error' : True,
                   'cores'         : 128,
                   'input_staging' : [path]
                  }
        pdesc = rp.ComputePilotDescription(pd_init)
        pilot = pmgr.submit_pilots(pdesc)

        umgr.add_pilots(pilot)
        idx  = 0
        cuds = list()
        while idx < n_smiles:

            cud = rp.ComputeUnitDescription()
            cud.cpu_processes  = 1
            cud.executable     = './theta_dock.py'
            cud.arguments      =  [smi_fname, tgt_fname, idx, chunk_size]
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
                                  {'source': 'pilot:///Model-generation/theta_dock.py',
                                   'target': 'unit:///theta_dock.py',
                                   'action': rp.LINK},
                                  ]
            cud.output_staging = [{'source': 'unit:///STDOUT',
                                   'target': 'client:///output/output.%d' % idx,
                                   'action': rp.TRANSFER}]
            cuds.append(cud)
            idx += chunk_size

        umgr.submit_units(cuds)
        umgr.wait_units()

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------

