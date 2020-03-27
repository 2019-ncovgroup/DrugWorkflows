#!/usr/bin/env python3

import os
import sys
import copy
import glob
import time
import signal

import numpy         as np
import threading     as mt

import radical.pilot as rp
import radical.utils as ru


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
class Request(object):

    # poor man's future
    # TODO: use proper future implementation


    # --------------------------------------------------------------------------
    #
    def __init__(self, work):

        self._uid    = ru.generate_id('req')
        self._work   = work
        self._state  = 'NEW'
        self._result = None


    # --------------------------------------------------------------------------
    #
    @property
    def uid(self):
        return self._uid


    @property
    def state(self):
        return self._state


    @property
    def result(self):
        return self._result


    # --------------------------------------------------------------------------
    #
    def as_dict(self):
        '''
        produce the request message to be sent over the wire to the workers
        '''

        return {'uid'   : self._uid,
                'state' : self._state,
                'result': self._result,
                'call'  : self._work['call'],
                'rank'  : self._work['rank'],
               }


    # --------------------------------------------------------------------------
    #
    def set_result(self, result, error):
        '''
        This is called by the master to fulfill the future
        '''

        self._result = result
        self._error  = error

        if error: self._state = 'FAILED'
        else    : self._state = 'DONE'


    # --------------------------------------------------------------------------
    #
    def wait(self):

        while self.state not in ['DONE', 'FAILED']:
            time.sleep(0.1)

        return self._result


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
    def __init__(self, cfg, dbase, n_workers):

        self._dbase     = dbase
        self._n_workers = n_workers

        # initialized the task overlay base class.  That base class will ensure
        # proper communication channels to the pilot agent.
        rp.task_overlay.Master.__init__(self)

        self._prof.prof('master_start', uid=self._uid)

        self._cfg['wf1'] = cfg
        self._cfg['wf1'] = cfg

      # # set up RU ZMQ Queues for request distribution and result collection
      # req_cfg = ru.Config(cfg={'channel'    : 'to_req',
      #                          'type'       : 'queue',
      #                          'uid'        : self._uid + '.req',
      #                          'path'       : os.getcwd(),
      #                          'stall_hwm'  : 0,
      #                          'bulk_size'  : 1})
      #
      # res_cfg = ru.Config(cfg={'channel'    : 'to_res',
      #                          'type'       : 'queue',
      #                          'uid'        : self._uid + '.res',
      #                          'path'       : os.getcwd(),
      #                          'stall_hwm'  : 0,
      #                          'bulk_size'  : 1})
      #
      # self._req_queue = ru.zmq.Queue(req_cfg)
      # self._res_queue = ru.zmq.Queue(res_cfg)

        req_queue_cfg = cfg=ru.read_json('../funcs_req_queue.cfg')
        res_queue_cfg = cfg=ru.read_json('../funcs_res_queue.cfg')

        self._req_addr_put = req_queue_cfg['put']
        self._req_addr_get = req_queue_cfg['get']

        self._res_addr_put = res_queue_cfg['put']
        self._res_addr_get = res_queue_cfg['get']

        # this master will put requests onto the request queue, and will get
        # responses from the response queue.  Note that the responses will be
        # delivered via an async callback (`self.result_cb`).
        self._req_put = ru.zmq.Putter('funcs_req_queue',
                                      self._req_addr_put, 
                                      log=self._log, 
                                      prof=self._prof)
        self._res_get = ru.zmq.Getter('funcs_req_queue',
                                      self._res_addr_get,
                                      cb=self.result_cb, 
                                      log=self._log, 
                                      prof=self._prof)

        # for the workers it is the opposite: they will get requests from the
        # request queue, and will send responses to the response queue.
        self._info = {'req_addr_get': self._req_addr_get,
                      'res_addr_put': self._res_addr_put}

        self._log.debug('info: %s', self._info)

        # make sure the channels are up before allowing to submit requests
        time.sleep(1)

        # prepare for operation
        self._fstate = '%s/status.json' % self._dbase
        self._state  = dict()      # state of all ranks
        self._req    = dict()      # keep track of open requests
        self._lock   = mt.RLock()  # lock the request and state dicts on updates


    # --------------------------------------------------------------------------
    #
    def sync(self):

        # safe current state to disk
        with self._lock:
            if self._state:
                self._log.debug('sync [%d]: %s', len(self._state),
                        self._state[sorted(self._state.keys())[0]])
            else:
                self._log.debug('sync [0]')

            try:
                ru.write_json(self._state, '%s.tmp' % self._fstate)
             #  os.system('ls -l %s.tmp %s' % (self._fstate, self._fstate))
                os.system('mv    %s.tmp %s' % (self._fstate, self._fstate))
             #  os.system('ls -l %s.tmp %s' % (self._fstate, self._fstate))
            except:
                self._log.exception('sync error')


    # --------------------------------------------------------------------------
    #
    def run(self):

        self._prof.prof('master_run_start', uid=self._uid)

        # insert workers into the agent.  The agent will schedule (place)
        # those workers and execute them.
        self.submit_workers()

        if not os.path.exists(self._fstate):
            self.sync()

        try:
            self._state = ru.Config(cfg=ru.read_json(self._fstate))
        except:
            self._state = dict()

        to_minimize = list()  # need to run minimization
        to_simulate = list()  # need to run mmgbsa simulations

        for rank in glob.glob('%s/rank*/' % self._dbase):


            rank = rank.rstrip('/')
            rid  = rank.split('/')[-1]
            if rid not in self._state:
                self._state[rid] = {'energy'  : None,  # unknown
                                    'simulate': None}  # not done yet

            info = self._state[rid]
            if   info['energy'  ] is None: to_minimize.append(rank)
            elif info['simulate'] is True: to_simulate.append(rank)

        # submit all minimization tasks first
        for rank in to_minimize:
            self.request('minimize', rank)

      # # submit all simulations tasks
      # for rank in to_simulate:
      #     self.request('simulate', rank)

        # all eligible tasks are submitted - now we just wait for the results to
        # come back.  If minimization results are positive, we may need to
        # submit new tasks (in self._result_cb) - but otherwise we just wait (in
        # `self.wait()`) until all tasks are done.

        # sync current state to disk
        self.sync()

        # TODO: wait for completion
        while len(self._req):
            self._log.debug('wait: %d', len(self._req))
            time.sleep(5)

        self._prof.prof('master_run_stop', uid=self._uid)

    # --------------------------------------------------------------------------
    #
    def submit_workers(self):
        '''
        submit workers, and pass the queue info as configuration file
        '''

        descr = copy.deepcopy(self._cfg['wf1']['worker'])
        descr['executable'] = '%s/wf1_worker.py' % os.getcwd()

        if not descr.get('environment'):
            descr['environment'] = dict()
        descr['environment']['PYTHONPATH'] = os.getcwd()

        self._log.debug('submit %s' % descr)

        self.submit(self._info, descr, self._n_workers)
      # self.wait(count=self._n_workers)
      # self.wait(count=1)

        self._log.debug('workers are up')


    # --------------------------------------------------------------------------
    #
    def request(self, call, rank):
        '''
        submit a work request to the request queue
        '''

        assert(call in ['minimize', 'simulate']), call

        rid  = rank.split('/')[-1]
        self._prof.prof('master_%s_req' % call[0:3], uid=self._uid, msg=rid)

        # create request and add to bookkeeping dict.  That response object will
        # be updated once a response for the respective request UID arrives.
        req = Request(work={'call'  : call,
                            'rank'  : rank})
        with self._lock:
            self._req[req.uid] = req

        self._log.info('req put %s %s: %s', call, rank, req.uid)
        # push the request message (here and dictionary) onto the request queue
        self._req_put.put(req.as_dict())

        # return the request to the master script for inspection etc.
        return req


    # --------------------------------------------------------------------------
    #
    def result_cb(self, msg):

        self._log.debug('=== result')

        # update result and error information for the corresponding request UID
        call = msg['call']
        rank = msg['rank']
        uid  = msg['uid']
        res  = msg['res']
        err  = msg['err']
        rid  = rank.split('/')[-1]

        self._prof.prof('master_%s_res' % call[0:3], uid=self._uid, msg=rid)
        self._log.info('res get %s %s: %s : %s : %s', call, rank, uid, res, err)

        # check if the request was a minimize or simulate call.  For minimiz,
        # evaluate the returned anergy and decide if we need to submit an
        # simulate task - if so, submit it.  For a simulate result, just mark
        # the state.

        with self._lock:

            self._req[uid].set_result(res, err)

            if call == 'minimize':

                if res is None: self._state[rid]['energy'] = np.nan
                else          : self._state[rid]['energy'] = res

                if res is None or res <= 0:
                    # no need to simulate this rank
                    self._log.debug('rank %s: min done', rid)
                    self._state[rid]['simulate'] = False
              # else:
              #     # got a positive energy: submit simulation
              #     self._log.debug('rank %s: req sim', rid)
              #     self._state[rid]['simulate'] = True
              #     self.request('simulate', rank)

            elif call == 'simulate':

                # just record the result
                self._log.debug('rank %s: sim done', rid)
                self._state[rid]['simulate'] = False

            self.sync()

            # request is done
            del(self._req[uid])


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # This master script currently runs as a task within a pilot allocation.
    # The purpose of this master is to (a) spawn a set or workers within the
    # same allocation, (b) to distribute work items (`hello` function calls) to
    # those workers, and (c) to collect the responses again.

    dbase     =     sys.argv[1]
    n_workers = int(sys.argv[2])
    target    =     sys.argv[3]

    cfg       = ru.read_json('config.json')[target]

    # create a master class instance - this will establish communitation to the
    # pilot agent
    master = MyMaster(cfg, dbase, n_workers)
    master.run()

    # simply terminate
    # FIXME: this needs to be cleaned up, should kill workers cleanly
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGKILL)
    os.kill(os.getpid(), signal.SIGTERM)


# ------------------------------------------------------------------------------

