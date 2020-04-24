#!/usr/bin/env python3

import os
import sys

import radical.utils as ru
import radical.pilot as rp

import pandas  as pd
import numpy   as np


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

        # initialized the task overlay base class.  That base class will ensure
        # proper communication channels to the pilot agent.
        rp.task_overlay.Master.__init__(self, cfg=cfg)

        print('%s: cfg from %s to %s' % (self._uid, cfg.idx, cfg.n_masters))


    # --------------------------------------------------------------------------
    #
    def create_work_items(self):

        world_size = self._cfg.n_masters
        rank       = self._cfg.idx
        workload   = self._cfg.workload

        # read the smi file for this master's index range, and send the
        # resulting pos indexes as task batches
        smiles_file = pd.read_csv('input_dir/' + workload.smiles)

        poss = np.array_split(list(range(smiles_file.shape[0])), world_size)[rank]

        i = 0
        for pos in poss:
            i += 1
            if i > 1024:
                break

            item = {'mode':  'call',
                    'data': {'method': 'hello',
                             'kwargs': {'pos': int(pos)}}}
            self.request(item)

        return


    # --------------------------------------------------------------------------
    #
    def result_cb(self, requests):

        # result callbacks can return new work items
        new_requests = list()
        for r in requests:
            print('result_cb %s: %s [%s]' % (r.uid, r.state, r.result))
          # print('work: %s' % r.work)

          # count = r.work['data']['kwargs']['count']
          # if count < 10:
          #     new_requests.append({'mode': 'call',
          #                          'data': {'method': 'hello',
          #                                   'kwargs': {'count': count + 100}}})

        return new_requests


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # This master script runs as a task within a pilot allocation.  The purpose
    # of this master is to (a) spawn a set or workers within the same
    # allocation, (b) to distribute work items (`hello` function calls) to those
    # workers, and (c) to collect the responses again.
    cfg_fname    = 'wf0.cfg'
    cfg          = ru.Config(cfg=ru.read_json(cfg_fname))
    cfg.idx      = int(sys.argv[1])

    # FIXME: worker startup should be moved into master
    workload   = cfg.workload
    n_nodes    = cfg.nodes
    cpn        = cfg.cpn
    gpn        = cfg.gpn
    descr      = cfg.worker_descr

    # add data staging to worker: link input_dir, impress_dir, and oe_license
    descr['arguments']     = ['wf0_worker.py']
    descr['input_staging'] = [
                               {'source': '%s/wf0_worker.py' % os.getcwd(),
                                'target': 'wf0_worker.py',
                                'action': rp.COPY,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.0'},
                               {'source': '%s/wf0.cfg' % os.getcwd(),
                                'target': 'wf0.cfg',
                                'action': rp.COPY,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.1'},
                               {'source': workload.input_dir,
                                'target': 'input_dir',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.2'},
                               {'source': workload.impress_dir,
                                'target': 'impress_md',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.3'},
                               {'source': workload.oe_license,
                                'target': 'oe_license.txt',
                                'action': rp.LINK,
                                'flags' : rp.DEFAULT_FLAGS,
                                'uid'   : 'sd.4'},
                              ]

    # one node is used by master.  Alternatively (and probably better), we could
    # reduce one of the worker sizes by one core.  But it somewhat depends on
    # the worker type and application workload to judge if that makes sense, so
    # we leave it for now.
    n_workers = int((n_nodes / cfg.n_masters) - 1)

    # create a master class instance - this will establish communitation to the
    # pilot agent
    master = MyMaster(cfg)

    # insert `n` worker tasks into the agent.  The agent will schedule (place)
    # those workers and execute them.  Insert one smaller worker (see above)
    # NOTE: this assumes a certain worker size / layout
    master.submit(descr=descr, count=n_workers, cores=cpn,     gpus=gpn)
    master.submit(descr=descr, count=1,         cores=cpn - 1, gpus=gpn)

    # wait until `m` of those workers are up
    # This is optional, work requests can be submitted before and will wait in
    # a work queue.
  # master.wait(count=nworkers)

    master.run()

    # simply terminate
    # FIXME: clean up workers


# ------------------------------------------------------------------------------

