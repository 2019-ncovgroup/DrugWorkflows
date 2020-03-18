#!/usr/bin/env python3

import os
import sys
import glob

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

    dbase_loc  = os.environ['PREFIX']
    dbase_path = '%s/%s' % (dbase_loc, dbase)
    work       = os.getcwd()  # NOTE: needs to live on a shared FS

    # we link all DB entries (ranks) which need minimization into work_minimize.
    # The workers will pick up a rank, move it to minimize_active and minimize
    # it.  If energy > 0, they'll write a stats file in `work_stats` and remove
    # the link.  If enery <= 0, they move the rank to work_mmgbsa.  workers
    # (potentially others) will pick up a rank from work_mmgbsa and move it to
    # work_mmgbsa_active, and run mmgbsa on it.  After completion they write
    # a file in work_stats and remove the rank link.
    #
    # FIXME: what is the output of all this?

    dir_min_new = '%s/work_minimize'        % work
    dir_min_act = '%s/work_minimize_active' % work
    dir_sim_new = '%s/work_mmgbsa'          % work
    dir_sim_act = '%s/work_mmgbsa_active'   % work
    dir_stats   = '%s/work_stats'           % work

    ru.rec_makedir(dir_min_new)
    ru.rec_makedir(dir_min_act)
    ru.rec_makedir(dir_sim_new)
    ru.rec_makedir(dir_sim_act)
    ru.rec_makedir(dir_stats  )

    # prepare the ranks to work on
    ranks = sorted(list(glob.glob('%s/rank*' % dbase_path)))  # [:60]

    # if no stats file exist, no link exists in work_minimize or work_mmgbsa,
    # then create a link in work_minimize
    # NOTE: this races on link check atomicity
    for rank in ranks:

        rbase = os.path.basename(rank)

        if  not os.path.exists('%s/%s' % (dir_min_new, rbase)) and \
            not os.path.exists('%s/%s' % (dir_sim_new, rbase)) and \
            not os.path.exists('%s/%s' % (dir_stats  , rbase)) :
            link(rank,         '%s/%s' % (dir_min_new, rbase))

    cfg        = ru.read_json('config.json')[target]
    model      = '%s/../../Model-generation' % os.getcwd()
    conda      = cfg['conda']
    cpn        = cfg['cpn']
    gpn        = cfg['gpn']

    n_tasks    = nodes * gpn

    session    = rp.Session()
    try:
        pmgr   = rp.PilotManager(session=session)
        umgr   = rp.UnitManager(session=session)
        pdinit = cfg['pilot']

        pdinit["cores"]        += nodes * cpn
        pdinit["gpus"]          = nodes * gpn
        pdinit["exit_on_error"] = True
        pdinit["input_staging"] = [model,
                                   'wf1_worker.sh',
                                   'wf1_task.sh',
                                   'wf1_task.py',
                                   'oe_license.txt'
                                  ]

        pdescs = rp.ComputePilotDescription(pdinit)
        pilots = pmgr.submit_pilots(pdescs)

        umgr.add_pilots(pilots)

        cuds = list()

        for t in range(n_tasks):

            udinit = cfg['task']
            udinit['cpu_processes'] = 1
            udinit['gpu_processes'] = 1
            udinit['executable']    = './wf1_worker.sh'
            udinit['arguments']     =  [conda, work]
            udinit['environment']   =  {'OE_LICENSE': 'oe_license.txt'}
            udinit['input_staging'] = [{'source': 'pilot:///Model-generation/input',
                                        'target': 'unit:///input',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///Model-generation/impress_md',
                                        'target': 'unit:///impress_md',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///oe_license.txt',
                                        'target': 'unit:///oe_license.txt',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_worker.sh',
                                        'target': 'unit:///wf1_worker.sh',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_task.sh',
                                        'target': 'unit:///wf1_task.sh',
                                        'action': rp.LINK},
                                       {'source': 'pilot:///wf1_task.py',
                                        'target': 'unit:///wf1_task.py',
                                        'action': rp.LINK},
                                      ]
            cud = rp.ComputeUnitDescription(udinit)
            cuds.append(cud)

        umgr.submit_units(cuds)
        umgr.wait_units()

    finally:
        session.close(download=True)
        pass


# ------------------------------------------------------------------------------

