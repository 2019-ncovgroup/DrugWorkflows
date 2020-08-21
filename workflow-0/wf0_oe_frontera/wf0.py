#!/usr/bin/env python3

import os
import sys
import glob
import pprint

import radical.utils as ru
import radical.saga  as rs
import radical.pilot as rp


global p_map
p_map = dict()  # pilot: [task, task, ...]


# ------------------------------------------------------------------------------
#
def unit_state_cb(unit, state):

    # terminate pilots once all masters running it are completed,

    global p_map

    if state not in rp.FINAL:
        return True

    print('unit state: %s -> %s' % (unit.uid, state))
    pilot = None
    for p in p_map:
        for u in p_map[p]:
            if u.uid == unit.uid:
                pilot = p
                break
        if pilot:
            break

    # every master should be associated with one pilot
    assert(pilot), [pilot.uid, unit.uid, pprint.pformat(pilot.as_dict())]

    to_cancel = True
    for u in p_map[pilot]:
        if u.state not in rp.FINAL:
            to_cancel = False
            break

    if to_cancel:
        print('cancel pilot %s' % pilot.uid)
        pilot.cancel()
    else:
        print('pilot remains active: %s' % pilot.uid)

    return True


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    cfg_file  = sys.argv[1]  # resource and workload config
    run_file  = sys.argv[2]  # runs for this campaign
    session   = None

    try:

        cfg       = ru.Config(cfg=ru.read_json(cfg_file))
        rec_path  = 'input/receptors.v7/'    # FIXME
        smi_path  = 'input/smiles/'           # FIXME
        runs      = list()

        with open(run_file, 'r') as fin:

            for line in fin.readlines():
                line  = line.strip()
                elems = line.split()
                if len(elems) != 4:
                    continue
                if elems[0] == '#':
                    continue

                receptor = str(elems[0])
                smiles   = str(elems[1])
                nodes    = int(elems[2])
                runtime  = int(elems[3])

                assert(receptor)
                assert(smiles)
                assert(nodes)
                assert(runtime)

                print('%s/%s.oeb' % (rec_path, receptor))
                print('%s/%s.csv' % (smi_path, smiles))
                assert(os.path.isfile('%s/%s.oeb' % (rec_path, receptor)))
                assert(os.path.isfile('%s/%s.csv' % (smi_path, smiles)))

                runs.append([receptor, smiles, nodes, runtime])

        session = rp.Session()
        pmgr    = rp.PilotManager(session=session)
        umgr    = rp.UnitManager(session=session)

        umgr.register_callback(unit_state_cb)


        # for each run in the campaign:
        #   - create pilot of requested size and runtime
        #   - create cfg with requested receptor and smiles
        #   - submit configured number of masters with that cfg on that pilot
        subs = dict()
        d    = rs.filesystem.Directory('ssh://frontera/scratch1/07305/rpilot/workflow-0-results')
        ls   = [str(u).split('/')[-1] for u in d.list()]

        workload  = cfg.workload

        for receptor, smiles, nodes, runtime in runs:

            print('=== %30s  %s' % (receptor, smiles))
            name = '%s_-_%s'     % (receptor, smiles)
            tgt  = '%s.%s.gz'    % (name, workload.output)
            rec  = False

            if tgt in ls:
                if workload.recompute:
                    rec += 1
                    d.move(tgt, tgt + '.bak')
                else:
                    print('skip      1 %s' % name)
                    continue

            if smiles in ls:
                if smiles not in subs:
                    subs[smiles] = [str(u).split('/')[-1]  for u in d.list('%s/*' % smiles)]
                if tgt in subs[smiles]:
                    if workload.recompute:
                        rec += 2
                        d.move('%s/%s'     % (smiles, tgt),
                               '%s/%s.bak' % (smiles, tgt))
                    else:
                        print('skip      2 %s' % name)
                        continue

          # if os.path.exists('results/%s.%s.gz' % (name, wofkload.output)):
          #     print('skip      3 %s' % name)
          #     continue

            if rec: print('recompute %d %s' % (rec, name))
            else  : print('compute   2 %s'  %       name)

            cpn       = cfg.cpn
            gpn       = cfg.gpn
            n_masters = cfg.n_masters

            # FIXME
            cfg.cpn = 30

            cfg.workload.receptor = '%s.oeb'  % receptor
            cfg.workload.smiles   = '%s.csv'  % smiles
            cfg.workload.name     = name
            cfg.nodes             = nodes
            cfg.runtime           = runtime

            ru.write_json(cfg, 'configs/wf0.%s.cfg' % name)

            pd = rp.ComputePilotDescription(cfg.pilot_descr)
            pd.cores   = nodes * cpn
            pd.gpus    = nodes * gpn
            pd.runtime = runtime

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
                                     {'source': 'configs/wf0.%s.cfg' % name,
                                      'target': 'wf0.cfg',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': workload.input_dir,
                                      'target': 'input_dir',
                                      'action': rp.LINK,
                                      'flags' : rp.DEFAULT_FLAGS}
                                    ]
                td.output_staging = [{'source': '%s.%s.gz'         % (name, workload.output),
                                      'target': 'results/%s.%s.gz' % (name, workload.output),
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS}]
                tds.append(td)

            tasks = umgr.submit_units(tds)
            p_map[pilot] = tasks

        # all pilots and masters submitted - wait for them to finish
        umgr.wait_units()

    finally:
        if session:
            session.close(download=True)


# ------------------------------------------------------------------------------

