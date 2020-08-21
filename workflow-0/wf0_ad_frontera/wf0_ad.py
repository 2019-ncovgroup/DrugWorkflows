#!/usr/bin/env python3

import os
import sys
import copy
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
        rec_path  = 'input/receptorsV5.1/'    # FIXME
        smi_path  = 'input/'                  # FIXME
        runs      = list()

        with open(run_file, 'r') as fin:

            for line in fin.readlines():

                elems = line.split()

                if not elems or elems[0] == '#':
                    continue
                print('\t'.join(elems))

                receptor = str(elems[0])
                smiles   = str(elems[1])
                nodes    = int(elems[2])
                runtime  = int(elems[3])

                assert(receptor)
                assert(smiles)
                assert(nodes)
                assert(runtime)

                smi = '%s/%s.csv'         % (cfg.workload.smi_path, smiles)
                rec = '%s/%s/%s_box.mol2' % (cfg.workload.rec_path,
                                             receptor, receptor)

                assert(os.path.isfile(rec)), rec
                assert(os.path.isfile(smi)), smi

                box, err, ret = ru.sh_callout('python3 ./mol2_to_box.py %s' % rec)
                assert(not ret), err

                runs.append([receptor, smiles, nodes, runtime, box])

        session = rp.Session()
        pmgr    = rp.PilotManager(session=session)
        umgr    = rp.UnitManager(session=session)

        umgr.register_callback(unit_state_cb)


        # for each run in the campaign:
        #   - create pilot of requested size and runtime
        #   - create cfg with requested receptor and smiles
        #   - submit configured number of masters with that cfg on that pilot
        subs = dict()
      # d    = rs.filesystem.Directory(cfg.workload.results)
      # ls   = [str(u).split('/')[-1] for u in d.list()]

        workload  = cfg.workload
        cpn       = cfg.cpn
        gpn       = cfg.gpn
      
        pds = list()
        for receptor, smiles, nodes, runtime, box in runs:
      
            pd = rp.ComputePilotDescription(copy.deepcopy(cfg.pilot_descr))
            pd.cores   = nodes * cpn
            pd.gpus    = nodes * gpn
            pd.runtime = runtime
            pds.append(pd)
      
        pilots = pmgr.submit_pilots(pds)
        umgr.add_pilots(pilots)


        pidx = 0
        for receptor, smiles, nodes, runtime, box in runs:

            pilot = pilots[pidx]
            pid   = pilot.uid
            pidx += 1

            name = '%s_-_%s'     % (receptor, smiles)
            tgt  = '%s.%s.gz'    % (name, workload.output)
            rec  = False

          # if tgt in ls:
          #     if workload.recompute:
          #         rec += 1
          #         d.move(tgt, tgt + '.bak')
          #     else:
          #         print('skip        %-30s [remote result]' % name)
          #         continue
          #
          # if smiles in ls:
          #     if smiles not in subs:
          #         subs[smiles] = [str(u).split('/')[-1]  for u in d.list('%s/*' % smiles)]
          #
          #     if tgt in subs[smiles]:
          #         if workload.recompute:
          #             rec += 2
          #             d.move('%s/%s'     % (smiles, tgt),
          #                    '%s/%s.bak' % (smiles, tgt))
          #         else:
          #             print('skip        %-30s [remote smiles result]' % name)
          #             continue
          #
          # if os.path.exists('results/%s.%s.gz' % (name, workload.output)):
          #     print('skip        %-30s [local result]' % name)
          #     continue

            if rec: print('recompute %d %-30s' % (rec, name))
            else  : print('compute     %-30s'  %       name)

            cfg.workload.name     = name
            cfg.workload.receptor = receptor
            cfg.workload.smiles   = smiles
            cfg.nodes             = nodes
            cfg.runtime           = runtime
            cfg.box               = box

            ru.write_json(cfg, 'configs/wf0.%s.cfg' % name)

            n_masters = cfg.n_masters

            tds = list()

            for i in range(n_masters):
                td = rp.ComputeUnitDescription(copy.deepcopy(cfg.master_descr))
                td.executable     = "python3"
                td.arguments      = ['wf0_ad_master.py', i]
                td.cpu_threads    = 1
                td.pilot          = pid
                td.input_staging  = [{'source': cfg.master,
                                      'target': 'wf0_ad_master.py',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': cfg.worker,
                                      'target': 'wf0_ad_worker.py',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': cfg.helper_1,
                                      'target': 'wf0_ad_helper_1.sh',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': cfg.prep,
                                      'target': 'wf0_ad_prep.sh',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': cfg.tar,
                                      'target': 'wf0_ad_prep.tar',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': 'configs/wf0.%s.cfg' % name,
                                      'target': 'wf0.cfg',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': 'mol2_to_box.py',
                                      'target': 'mol2_to_box.py',
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS},
                                     {'source': workload.inputs,
                                      'target': 'inputs',
                                      'action': rp.LINK,
                                      'flags' : rp.DEFAULT_FLAGS}
                                    ]
                td.output_staging = [{'source': '%s.tgz'         % (name),
                                      'target': 'results/%s.tgz' % (name),
                                      'action': rp.TRANSFER,
                                      'flags' : rp.DEFAULT_FLAGS}]
                td.post_exec = ['tar zcvf %s.tgz *.sdf worker.*/*.sdf' % name]
                tds.append(td)

            tasks = umgr.submit_units(tds)
            p_map[pilot] = tasks

        # all pilots and masters submitted - wait for them to finish
        umgr.wait_units()

    finally:
        if session:
            session.close(download=True)


# ------------------------------------------------------------------------------

