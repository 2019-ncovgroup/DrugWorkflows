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
    # Frontera
    path       = '/home/merzky/projects/covid/Model-generation/'
    conda      = '/home/merzky/.miniconda3/'
    # Stampede2
    path       = '/home1/01083/tg803521/radical/covid/Model-generation/'
    conda      = '/home1/01083/tg803521/.miniconda3/'
    # Comet
    path       = '/home/mturilli/github/Model-generation'
    conda      = '/home/mturilli/.miniconda3/'

    smiles     = pd.read_csv('%s/%s' % (path, smi_fname), sep=' ', header=None)
    n_smiles   = smiles.shape[0]

    n_pilots   = 10

    task_size  = 1
    chunk_size = 10000

    done       = 0
    idx        = 0

    while done < n_smiles:

        session    = rp.Session()

        try:
            pmgr   = rp.PilotManager(session=session)
            umgr   = rp.UnitManager(session=session)
            pd_init = {'resource'      : 'xsede.comet_ssh',
                       'runtime'       : 60,
                       'exit_on_error' : True,
                       'cores'         : 24 * 5 + 24  * 10,
                       'project'       : 'TG-MCB090174',
                       'queue'         : 'compute',
                       'input_staging' : [path]
                      }
            pdescs = [rp.ComputePilotDescription(pd_init) for i in range(n_pilots)]
            pilots = pmgr.submit_pilots(pdescs)

            umgr.add_pilots(pilots)

            chunk = 0
            cuds  = list()
            while chunk < chunk_size * n_pilots:

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
                idx   += task_size
                chunk += task_size

            umgr.submit_units(cuds)
            umgr.wait_units()

        finally:
            session.close(download=True)
            done += chunk


# ------------------------------------------------------------------------------

