#!/usr/bin/env python3

import os
import sys

os.system('which python')
print(os.environ.get('PYTHONPATH'))

import numpy as np

from impress_md import interface_functions as iface


import radical.utils as ru
import radical.pilot as rp


# ------------------------------------------------------------------------------
#
class MyWorker(rp.task_overlay.Worker):
    '''
    This class provides the required functionality to execute work requests.
    In this simple example, the worker only implements a single call: `hello`.
    '''


    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg):

        # ensure that communication to the pilot agent is up and running, so
        # that the worker can respond to management commands (termination).
        # This will also read the passed config file and make it available as
        # `self._cfg`.
        rp.task_overlay.Worker.__init__(self, cfg)

        self._prof.prof('worker_start', uid=self._uid)


    # --------------------------------------------------------------------------
    #
    def initialize(self):
        '''
        This method is called during base class construction.  All agent
        communication channels are available at this point.

        We use this point to connect to the request / response ZMQ queues.  Note
        that incoming requests will trigger an async callback `self.request_cb`.
        '''

        self._req_get = ru.zmq.Getter('funcs_req_queue',
                                      self._info.req_addr_get,
                                      cb=self.request_cb, 
                                      log=self._log, 
                                      prof=self._prof)
        self._res_put = ru.zmq.Putter('funcs_res_queue',
                                      self._info.res_addr_put, 
                                      log=self._log, 
                                      prof=self._prof)

        self._log.info('initialized: %s', self._info)
        self._prof.prof('worker_init', uid=self._uid)

        # the worker can return custom information which will be made available
        # to the master.  This can be used to communicate, for example, worker
        # specific communication endpoints.
        return {'foo': 'bar'}


    # --------------------------------------------------------------------------
    #
    def request_cb(self, msg):
        '''
        This implementation only understands a single request type: 'hello'.
        It will run that request and immediately return a respone message.
        All other requests will immediately trigger an error response.
        '''

        uid  = msg['uid']
        call = msg['call']
        rank = msg['rank']
        val  = np.NaN
        err  = None
        rid  = rank.split('/')[-1]

        self._log.info('req get %s %s: %s', call, rank, uid)

        try:
            if call == 'minimize':
                self._prof.prof('worker_min_start', uid=self._uid, msg=rid)
                val = iface.RunMinimization_(rank, rank, write=True, gpu=True)
                self._prof.prof('worker_min_stop',  uid=self._uid, msg=rid)

            elif msg['call'] == 'simulate':
                self._prof.prof('worker_sim_start', uid=self._uid, msg=rid)
                val = iface.RunMMGBSA_(rank, rank, gpu=True, niters=5000)
                self._prof.prof('worker_sim_stop',  uid=self._uid, msg=rid)

        except Exception as e:
            self._log.exception('call failed')
            err = str(e)

        res = {'call': call,
               'rank': rank,
               'uid' : uid,
               'res' : val,
               'err' : err}

        self._log.info('res put %s %s: %s : %s : %s', call, rank, uid, val, err)
        self._res_put.put(res)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # the `info` dict is passed to the worker as config file.
    # Create the worker class and run it's work loop.
    worker = MyWorker(sys.argv[1])
    worker.run()


# ------------------------------------------------------------------------------

