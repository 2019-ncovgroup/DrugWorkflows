#!/usr/bin/env python3

import os
import sys
import glob

import radical.utils as ru
import radical.pilot as rp

# import pandas  as pd
# import numpy   as np


# This script has to run as a task within an pilot allocation, and is
# a demonstration of a task overlay within the RCT framework.
# It will:
#
#   - create a master which bootstrappes a specific communication layer
#   - insert n workers into the pilot (again as a task)
#   - perform RPC handshake with those workers
#   - send RPC requests to the workers
#   - terminate the worker
#
# The worker itself is an external program which is not covered in this code.


# ------------------------------------------------------------------------------
#
class MyMaster(rp.task_overlay.Master):
    '''
    This class provides the communication setup for the task overlay: it will
    set up the request / response communication queus and provide the endpoint
    information to be forwarded to the workers.
    '''

    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg):

        print('ctor 1')
        # initialized the task overlay base class.  That base class will ensure
        # proper communication channels to the pilot agent.
        rp.task_overlay.Master.__init__(self, cfg=cfg)

        print('%s: cfg from %s to %s' % (self._uid, cfg.idx, cfg.n_masters))

        self.parse_csv()

        # prepare local storage
        out, err, ret = ru.sh_callout("sh ./wf0_ad_prep.sh")
        self._log.debug('=== prep: %s\nout: %s\nerr: %s', ret, out, err)


    # --------------------------------------------------------------------------
    #
    def parse_csv(self):

        workload = self._cfg.workload
        fname    = 'input_dir/' + workload.smiles + '.csv'

        # build indexes
        self._idxs = list()
        with open(fname) as fin:
            while True:
                self._idxs.append(fin.tell())
                line = fin.readline()
                if line.startswith('SMILES,'): continue  # header
                if not line                  : break     # EOF

        self._idxs.pop()   # EOF

        # not all SMILES files have headers,
        # so we hardcode the SMILES and NAME columns
        self._cfg.smi_col = 0
        self._cfg.lig_col = 1


    # --------------------------------------------------------------------------
    #
    def create_work_items(self):

        self._prof.prof('create_start')

        world_size = self._cfg.n_masters
        name       = self._cfg.name
        rank       = self._cfg.idx

        # check the smi file for this master's index range, and send the
        # resulting pos indexes as task batches

        protein = self._cfg.workload.receptor

        # read list of known indicees
        known = list()
        fidx  = '%s/%s.idx' % (self._cfg.workload.indexes, name)
        if os.path.isfile(fidx):
            with open(fidx, 'r') as fin:
                for line in fin.readlines():
                    line = line.strip()
                    if not line.endswith('.idx'):
                        self._log.error('invalid idx [%s]', line)
                    idx = int(line[:-4])
                    known.append(idx)

        # write known indexes for debugging
        with open('./known.idx', 'w') as fout:
            for idx in known:
                fout.write('%d\n' % int(idx))

        # fields=${mol2_to_box.py 3CLPro_6LU7_AB_1_F_box.mol2}
        # export DC_PROTEIN=3CLPro_6LU7_AB_1_F
        # export DC_CENTER=${fields[0]}
        # export DC_POINTS=${fields[1]}

        out, err, ret = ru.sh_callout('./mol2_to_box.py input_dir/%s/%s_box.mol2'
                                     % (protein, protein))
        assert(not ret), err

        center, points = out.strip().split(' ', 1)
        assert(center)
        assert(points)

        reqs = list()
        pos  = rank
        npos = len(self._idxs)
        while pos < npos:

            if pos in known:
                self.log('create: %8d skip', pos)
                continue

            self.log('create: %8d new', pos)

          # if pos < 7800:
          #     pos += 1
          #     continue
          #
          # if pos >= 1024 * 128:
          #     break

            # def autodock(self, uid, smiles_idx, protein, center, points,
            #                    residues=None):
            uid  = 'request.%08d' % pos
            item = {'uid' :   uid,
                    'mode':  'call',
                    'data': {'method': 'autodock',
                             'kwargs': {'uid'       : uid,
                                        'pos'       : pos,
                                        'off'       : self._idxs[pos],
                                        'protein'   : protein,
                                        'center'    : center,
                                        'points'    : points,
                                        'residues'  : None}}}

            reqs.append(item)

            if len(reqs) > 1024:
                self.request(reqs)
                reqs = list()

            pos += world_size

        # push remaining requests
        if reqs:
            self.request(reqs)

        self._prof.prof('create_stop')


    # --------------------------------------------------------------------------
    #
    def result_cb(self, requests):

        # result callbacks can return new work items
        new_requests = list()
        for r in requests:
            sys.stdout.write('result_cb %s: %s [%s]\n' % (r.uid, r.state, r.result))
            sys.stdout.flush()

          # count = r.work['data']['kwargs']['count']
          # if count < 10:
          #     new_requests.append({'mode': 'call',
          #                          'data': {'method': 'autodock',
          #                                   'kwargs': {'count': count + 100}}})

        return new_requests


# ------------------------------------------------------------------------------
#
def main():

    print('main')

    # This master script runs as a task within a pilot allocation.  The purpose
    # of this master is to (a) spawn a set or workers within the same
    # allocation, (b) to distribute work items (`autodock` function calls) to
    # those workers, and (c) to collect the responses again.
    cfg_fname    = 'wf0.cfg'
    cfg          = ru.Config(cfg=ru.read_json(cfg_fname))
    cfg.idx      = int(sys.argv[1])

    # FIXME: worker startup should be moved into master
    workload   = cfg.workload
    rec        = cfg.workload.receptor
    n_nodes    = cfg.nodes
    cpn        = cfg.cpn
    gpn        = cfg.gpn
    descr      = cfg.worker_descr

    # add data staging to worker
    descr['arguments']     = ['wf0_ad_worker.py']
    descr['cpu_threads']   = 1
    descr['input_staging'] = [
                               {'source': '%s/wf0_ad_worker.py' % os.getcwd(),
                                'target': 'wf0_ad_worker.py',
                                'action': rp.COPY,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.0'},
                               {'source': '%s/wf0.cfg' % os.getcwd(),
                                'target': 'wf0.cfg',
                                'action': rp.COPY,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.1'},
                               {'source': '%s/wf0_ad_helper_1.sh' % os.getcwd(),
                                'target': 'wf0_ad_helper_1.sh',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.2'},
                               {'source': '%s/wf0_ad_prep.sh' % os.getcwd(),
                                'target': 'wf0_ad_prep.sh',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.3'},
                               {'source': '%s/wf0_ad_prep.tar' % os.getcwd(),
                                'target': 'wf0_ad_prep.tar',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.4'},
                               {'source': workload.input_dir,
                                'target': 'input_dir',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.5'},
                               {'source': 'input_dir/%s/%s.pdbqt' % (rec, rec),
                                'target': './',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.6'},
                              ]

    # one node is used by master.  Alternatively (and probably better), we could
    # reduce one of the worker sizes by one core.  But it somewhat depends on
    # the worker type and application workload to judge if that makes sense, so
    # we leave it for now.
    n_workers = int((n_nodes / cfg.n_masters) - 1)

    # create a master class instance - this will establish communitation to the
    # pilot agent
    master = MyMaster(cfg)
    print(1)

    # insert `n` worker tasks into the agent.  The agent will schedule (place)
    # those workers and execute them.  Insert one smaller worker (see above)
    # NOTE: this assumes a certain worker size / layout
    master.submit(descr=descr, count=n_workers, cores=cpn,     gpus=gpn)
    master.submit(descr=descr, count=1,         cores=cpn - 1, gpus=gpn)

    # wait until `m` of those workers are up
    # This is optional, work requests can be submitted before and will wait in
    # a work queue.
    print('wait')
    master.wait(count=n_workers + 1)
    print('run')

    master.run()

    # simply terminate
    # FIXME: clean up workers


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    try:
        main()

    except Exception as e:
        print('ERROR: %s' % e)
        raise


# ------------------------------------------------------------------------------

