#!/usr/bin/env python3

import os
import sys
import math
import pandas as pd

import radical.pilot as rp
import radical.utils as ru


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    cfg_fname   =     sys.argv[1]   # config file
    target      =     sys.argv[2]   # target HPC machine
    smi_fname   =     sys.argv[3]   # file with smiles
    tgt_fname   =     sys.argv[4]   # target receptor
    o_poses     =     sys.argv[5]   # output poses for theta_dock.py??

    idx_start   = int(sys.argv[6])  # start index of smi file
    n_pilots    = int(sys.argv[7])  # number of pilots
    n_tasks     = int(sys.argv[8])  # tasks per pilot (1 task = 1 CU)
    n_samples   = int(sys.argv[9])  # samples per task
    specfile    = ''                # gaps file from previous runs

    if len(sys.argv) > 10:
        n_samples = 0
        specfile  = sys.argv[10]

    # Staging directories on the remote machine
    r_smi_dir = '/scratch1/07305/rpilot/Model-generation/input'
    r_mod_dir = '/scratch1/07305/rpilot/Model-generation'
    r_wf0_dir = '/scratch1/07305/rpilot/DrugWorfklows/workflow-0'
    r_gap_dir = '%s/results/discovery_set_db-2' % r_wf0_dir

    cfg         = ru.read_json(cfg_fname)
    model       = '%s/Model-generation' % os.getcwd()
    conda       = cfg[target]['conda']
    cpn         = cfg[target]['cpn']

    idx         = idx_start
    smiles      = pd.read_csv('%s/%s' % (model, smi_fname))#, sep=' ')#, header=None)
    
    assert(idx_start < smiles.shape[0]), [idx_start, smiles.shape[0]]

    session    = rp.Session()
    try:
        # security context 
        # if cfg[target]['user_ssh'] and cfg[target]['pilot']['access_schema'] == 'ssh':
        #    ctx = rp.Context('ssh', {'user_id': cfg[target]['user_ssh']})
        #    session.add_context(ctx)

        pmgr   = rp.PilotManager(session=session)
        umgr   = rp.UnitManager(session=session)
        pdinit = cfg[target]['pilot']

        # pilot cores are agent cores configured in config.json, + worker nodes
        cores  = pdinit['cores'] + (n_tasks * cpn)

        pdinit["cores"]         = cores
        pdinit["exit_on_error"] = True
        # pdinit["input_staging"] = [
        #        model,
        #        'smi.sh',
        #        'theta_dock.sh',
        #        'theta_dock.py',
        #        'oe_license.txt'
        #       ]
        # if specfile:
        #    pdinit["input_staging"].append(specfile)

        print('%d pilots: %d cores on %d nodes' % (n_pilots, cores, cores/cpn))

        pdescs = [rp.ComputePilotDescription(pdinit) for i in range(n_pilots)]
        pilots = pmgr.submit_pilots(pdescs)

        umgr.add_pilots(pilots)

        uids = n_pilots * n_tasks
        for p in range(n_pilots):

            cuds = list()

            for t in range(n_tasks):

                uid = p * n_tasks + t

                idx = idx_start \
                    + (p * n_tasks * n_samples) \
                    + (t * n_samples)
                print(p, t, idx, n_samples)

                cud = rp.ComputeUnitDescription()
                cud.cpu_processes  = 1
                cud.cpu_threads    = cpn
                cud.executable     = './theta_dock.sh'
                cud.arguments      =  [conda, smi_fname, tgt_fname,
                                       cpn, idx, n_samples, uid, uids, specfile]
                cud.environment    =  {'OE_LICENSE': 'oe_license.txt'}
                cud.input_staging  = [{'source': 'file://%s'                % r_smi_dir,  # 'pilot:///Model-generation/input',
                                       'target': 'unit:///input',
                                       'action': rp.LINK},
                                      {'source': 'file://%s/impress_md'     % r_mod_dir,  # 'pilot:///Model-generation/impress_md',
                                       'target': 'unit:///impress_md',
                                       'action': rp.LINK},
                                      {'source': 'file://%s/oe_license.txt' % r_wf0_dir,  # 'pilot:///oe_license.txt',
                                       'target': 'unit:///oe_license.txt',
                                       'action': rp.LINK},
                                      {'source': 'file://%s/theta_dock.sh'  % r_wf0_dir,  # 'pilot:///theta_dock.sh',
                                       'target': 'unit:///theta_dock.sh',
                                       'action': rp.LINK},
                                      {'source': 'file://%s/theta_dock.py'  % r_wf0_dir,  # 'pilot:///theta_dock.py',
                                       'target': 'unit:///theta_dock.py',
                                       'action': rp.LINK},
                                      {'source': 'file://%s/smi.sh'         % r_wf0_dir,  # 'pilot:///smi.sh',
                                       'target': 'unit:///smi.sh',
                                       'action': rp.LINK},
                                      ]
                if specfile:
                    cud.input_staging.append({
                        'source': 'file://%s/%s' % (r_gap_dir, specfile),  # 'pilot:///%s' % specfile,
                        'target': 'unit:///specfile',
                        'action': rp.LINK})

                cuds.append(cud)

            # chunk defined for pilot
            print('submit %d tasks as chunk %d' % (len(cuds), p))
            umgr.submit_units(cuds)

        # all chunks submitted to pilots
        print('wait all')
        umgr.wait_units()

    finally:
        session.close(download=True)
        pass


# ------------------------------------------------------------------------------

