#!/usr/bin/env python3

import os
import sys
import glob
import time

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


def log(data):
    sys.stdout.write('=== %s\n' % data)
    sys.stdout.flush()



# ------------------------------------------------------------------------------
#
class MyMaster(rp.task_overlay.Master):
    '''
    This class provides the communication setup for the task overlay: it will
    set up the request / response communication queues and provide the endpoint
    information to be forwarded to the workers.
    '''

    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg):

        log('init 1')

        # initialized the task overlay base class.  That base class will ensure
        # proper communication channels to the pilot agent.
        rp.task_overlay.Master.__init__(self, cfg=cfg)

        log('%s: cfg from %s to %s' % (self._uid, cfg.idx, cfg.n_masters))

        self.parse_csv()


    # --------------------------------------------------------------------------
    #
    def parse_csv(self):

        workload = self._cfg.workload
        fname    = 'input_dir/smiles/%s.csv' % workload.smiles
        iname    = '%s.idx' % fname
        header   = None
        idxs     = list()
        i        = 0

        if os.path.isfile(iname):
            # read indexes
            log('using cached index')
            with open(fname) as fin:
                header = fin.readline()
            with open(iname, 'r') as fin:
                idxs = [int(line) for line in fin.readlines()]
            idxs.pop()   # EOF

        else:
            # build indexes
            log('read start')
            with open(fname) as fin:
                header = fin.readline()
                while True:
                    idxs.append(fin.tell())
                    line = fin.readline()
                    if not line  : break
                    if not i % 1000000:
                        log('read %d' % i)
                    i += 1
                  # if i > 10000:
                  #     break  # FIXME
            log('read stop')

            idxs.pop()   # EOF

        self._idxs        = idxs
        self._cfg.columns = header.strip('\n').split(',')

        self._cfg.smi_col = -1
        self._cfg.lig_col = -1

        for idx,col in enumerate(self._cfg.columns):
            if 'smile' in col.lower():
                self._cfg.smi_col = idx
                break

        for idx,col in enumerate(self._cfg.columns):
            if 'id'    in col.lower() or \
               'title' in col.lower() or \
               'name'  in col.lower():
                self._cfg.lig_col = idx
                break

        assert(self._cfg.smi_col >= 0)
        assert(self._cfg.lig_col >= 0)

        log('parse done')
        

    # --------------------------------------------------------------------------
    #
    def create_work_items(self):

        log('create_start')
        self._prof.prof('create_start')

        world_size = self._cfg.n_masters
        name       = self._cfg.workload.name
        rank       = self._cfg.idx
        chunk      = self._cfg.workload.chunksize

        # check the smi file for this master's index range, and send the
        # resulting pos indexes as task batches

        protein = self._cfg.workload.receptor
        smiles  = self._cfg.workload.smiles

        # read list of known indicees
        known = list()
        fidx  = '%s/%s/%s.idx' % (self._cfg.workload.results, smiles, name)
        self._log.debug('fidx: %s', fidx)

        if os.path.isfile(fidx):
            with open(fidx, 'r') as fin:
                for line in fin.readlines():
                    known.append(int(line))

        known   = set(known)
        all_pos = set(range(0, len(self._idxs)))
        new_pos = all_pos.difference(known)
        npos    = len(new_pos)

        # write known indexes for debugging
        with open('./known.idx', 'w') as fout:
            for idx in known:
                fout.write('%d\n' % int(idx))

        # index access needs list, not set
        new_pos = list(new_pos)

        # write new indexes for debugging
        with open('./new.idx', 'w') as fout:
            for idx in new_pos:
                fout.write('%d\n' % idx)

        self._todo = 0
        self._done = 0

        idx  = rank
        idxs = list()
        reqs = list()
        while idx < npos:

            pos  = new_pos[idx]
            off  = self._idxs[pos]
            idx += world_size

            idxs.append([idx, pos, off])

            if len(idxs) >= chunk:

                # The lowest index is used as basis for the request ID, it
                # identifies the batch of smiles packed into that request (bid).
                uid  = 'request.%06d' % idxs[0][0]
                item = {'uid'  :   uid,
                        'mode' :  'call',
                        'cores': 1,
                        'gpus' : 1, 
                        'data' : {'method': 'dock',
                                  'kwargs': {'idxs': idxs,
                                             'bid' : uid}}}
                self.request(item)
                idxs  = list()
                self._todo += 1

                self._log.debug('=== push bid %s', uid)

              # # FIXME AM:
              # break

        # request remaining indexes (likely fewer than `chunk`)
        if idxs:
            uid  = 'request.%06d' % idxs[0][0]
            item = {'uid'  :   uid,
                    'mode' :  'call',
                    'cores': 1,
                    'gpus' : 1, 
                    'data' : {'method': 'dock',
                              'kwargs': {'idxs': idxs,
                                         'bid': uid}}}
            self._log.debug('=== push bid %s', uid)
            self.request(item)
            self._todo += 1

        log('create_stop')
        self._prof.prof('create_stop')


    # --------------------------------------------------------------------------
    #
    def result_cb(self, requests):

        # result callbacks can return new work items
        new_requests = list()
        for r in requests:
            self._done += 1
            log('result_cb %s: %s [%s]\n' % (r.uid, r.state, r.result))

          # count = r.work['data']['kwargs']['count']
          # if count < 10:
          #     self._todo += 1
          #     new_requests.append({'mode': 'call',
          #                          'data': {'method': 'dock',
          #                                   'kwargs': {'count': count + 100}}})

        self._log.debug('=== term check: %d >= %d', self._done, self._todo)
        if self._done >= self._todo:
            self._log.debug('=== term check: terminate')
            self.terminate()

        return new_requests



## # ------------------------------------------------------------------------------
## #
## if __name__ == '__main__':
## 
##     log('=== start main 0')
## 
##     # This master script runs as a task within a pilot allocation.  The purpose
##     # of this master is to (a) spawn a set or workers within the same
##     # allocation, (b) to distribute work items (`hello` function calls) to those
##     # workers, and (c) to collect the responses again.
##     cfg_fname    = str(sys.argv[1])
##     cfg          = ru.Config(cfg=ru.read_json(cfg_fname))
##     cfg.rank     = int(sys.argv[2])
## 
##     log('=== start main 1')
## 
##     n_workers  = cfg.n_workers
##     cpn        = cfg.cpn
##     gpn        = cfg.gpn
##     descr      = cfg.worker_descr
##     worker     = 'wf0_worker.py'
##     pwd        = os.getcwd()
## 
##     log('=== start main 2')
##     # add data staging to worker: link input_dir, impress_dir, and oe_license
##     descr['arguments']     = [worker]
##   # descr['input_staging'] = [
##   #                            {'source': '%s/%s' % (pwd, worker),
##   #                             'target': worker,
##   #                             'action': rp.COPY,
##   #                             'flags' : rp.DEFAULT_FLAGS,
##   #                             'uid'   : 'sd.0'},
##   #                            {'source': '%s/%s' % (pwd, cfg_fname),
##   #                             'target': cfg_fname,
##   #                             'action': rp.COPY,
##   #                             'flags' : rp.DEFAULT_FLAGS,
##   #                             'uid'   : 'sd.1'},
##   #                           ]
## 
##     # one node is used by master.  Alternatively (and probably better), we could
##     # reduce one of the worker sizes by one core.  But it somewhat depends on
##     # the worker type and application workload to judge if that makes sense, so
##     # we leave it for now.
## 
##     # create a master class instance - this will establish communication to the
##     # pilot agent
##     master = MyMaster(cfg)
##     log('=== start main 3')
## 
##     # insert `n` worker tasks into the agent.  The agent will schedule (place)
##     # those workers and execute them.  Insert one smaller worker (see above)
##     # NOTE: this assumes a certain worker size / layout
##     print('workers: %d' % n_workers)
##     master.submit(descr=descr, count=n_workers, cores=cpn,     gpus=gpn)
##   # master.submit(descr=descr, count=1,         cores=cpn - 1, gpus=gpn)
##     log('=== start main 4')
## 
##     # wait until `m` of those workers are up
##     # This is optional, work requests can be submitted before and will wait in
##     # a work queue.
##   # master.wait(count=nworkers)
## 
##     master.run()
## 
##     # simply terminate
##     # FIXME: clean up workers


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    log('master starts')

    # This master script runs as a task within a pilot allocation.  The purpose
    # of this master is to (a) spawn a set or workers within the same
    # allocation, (b) to distribute work items (`dock` function calls) to those
    # workers, and (c) to collect the responses again.
    cfg_fname    = 'wf0.cfg'
    cfg          = ru.Config(cfg=ru.read_json(cfg_fname))
    cfg.idx      = int(sys.argv[1])

    # FIXME: worker startup should be moved into master
    workload   = cfg.workload
    smt        = cfg.smt
    cpw        = cfg.cpw
    gpw        = cfg.gpw
    descr      = cfg.worker_descr

    # one node is used by master.  Alternatively (and probably better), we could
    # reduce one of the worker sizes by one core.  But it somewhat depends on
    # the worker type and application workload to judge if that makes sense, so
    # we leave it for now.
    n_workers = cfg.n_workers
    log('n_workers: %d' % n_workers)

    # create a master class instance - this will establish communitation to the
    # pilot agent
    master = MyMaster(cfg)

    # insert `n` worker tasks into the agent.  The agent will schedule (place)
    # those workers and execute them.  Insert one smaller worker (see above)
    # NOTE: this assumes a certain worker size / layout
    log('smt: %d' % smt)
    log('cpw: %d' % cpw)
    log('gpw: %d' % gpw)
    master.submit(descr=descr, count=n_workers, cores=cpw * smt,     gpus=gpw)

    # wait until `m` of those workers are up
    # This is optional, work requests can be submitted before and will wait in
    # a work queue.
  # master.wait(count=nworkers)

    master.run()

    log('run completed')

    # simply terminate
    # FIXME: clean up workers

    # collect sdf files
    # os.system('sh -c "cat out.worker.*.sdf | gzip > %s.sdf.gz"' % workload.name)


# ------------------------------------------------------------------------------

