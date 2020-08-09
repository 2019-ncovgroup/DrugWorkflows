import sys
import pprint
import cProfile

import matplotlib.pyplot as plt
import numpy             as np

import radical.utils     as ru
import radical.pilot     as rp
import radical.analytics as ra

from   radical.utils.profile import *
from   radical.pilot.states  import *

# ------------------------------------------------------------------------------
#
# absolute utilization: number of core hours per activity
# relative utilization: percentage of total pilot core hours
#
ABSOLUTE = False

# ------------------------------------------------------------------------------
#
# pilot and unit activities: core hours are derived by multiplying the
# respective time durations with pilot size / unit size.  The 'idle' utilization
# and the 'agent' utilization are derived separately.
#
# Note that durations should add up to the `x_total` generations to ensure
# accounting for the complete unit/pilot utilization.
#
PILOT_DURATIONS = {
        'p_total'     : [{STATE: None,            EVENT: 'bootstrap_1_start'},
                         {STATE: None,            EVENT: 'bootstrap_1_stop' }],

        'p_boot'      : [{STATE: None,            EVENT: 'bootstrap_1_start'},
                         {STATE: None,            EVENT: 'sync_rel'         }],
        'p_setup_1'   : [{STATE: None,            EVENT: 'sync_rel'         },
                         {STATE: None,            EVENT: 'orte_dvm_start'   }],
        'p_orte'      : [{STATE: None,            EVENT: 'orte_dvm_start'   },
                         {STATE: None,            EVENT: 'orte_dvm_ok'      }],
        'p_setup_2'   : [{STATE: None,            EVENT: 'orte_dvm_ok'      },
                         {STATE: PMGR_ACTIVE,     EVENT: 'state'            }],
        'p_uexec'     : [{STATE: PMGR_ACTIVE,     EVENT: 'state'            },
                         {STATE: None,            EVENT: 'cmd'              }],
        'p_term'      : [{STATE: None,            EVENT: 'cmd'              },
                         {STATE: None,            EVENT: 'bootstrap_1_stop' }]}

UNIT_DURATIONS = {
        'u_total'     : [{STATE: None,            EVENT: 'schedule_ok'      },
                         {STATE: None,            EVENT: 'unschedule_stop'  }],

        'u_equeue'    : [{STATE: None,            EVENT: 'schedule_ok'      },
                         {STATE: AGENT_EXECUTING, EVENT: 'state'            }],
        'u_eprep'     : [{STATE: AGENT_EXECUTING, EVENT: 'state'            },
                         {STATE: None,            EVENT: 'exec_start'       }],
        'u_exec_rp'   : [{STATE: None,            EVENT: 'exec_start'       },
                         {STATE: None,            EVENT: 'cu_start'         }],
        'u_exec_cu'   : [{STATE: None,            EVENT: 'cu_start'         },
                         {STATE: None,            EVENT: 'cu_exec_start'    }],
        'u_exec_orte' : [{STATE: None,            EVENT: 'cu_exec_start'    },
                         {STATE: None,            EVENT: 'app_start'        }],
        'u_exec_app'  : [{STATE: None,            EVENT: 'app_start'        },
                         {STATE: None,            EVENT: 'app_stop'         }],
        'u_unschedule': [{STATE: None,            EVENT: 'app_stop'         },
                         {STATE: None,            EVENT: 'unschedule_stop'  }]}

DERIVED_DURATIONS = ['p_agent', 'p_idle', 'p_setup']

TRANSLATE_KEYS    = {
                     'p_agent'     : '* agent nodes',
                     'p_boot'      : '* pilot bootstrap',
                     'p_setup'     : '* pilot setup',
                     'p_orte'      : '* orte  setup',
                     'p_term'      : '* pilot termination',
                     'p_idle'      : '* pilot idle',

                     'u_equeue'    : 'SchedulerQueing CU',
                     'u_eprep'     : '* CU preparation',
                     'u_exec_rp'   : 'Executor Spawning CU',
                     'u_exec_cu'   : 'OS Spawning CU',
                     'u_exec_orte' : '* CU execution (ORTE)',
                     'u_exec_app'  : 'Executable Executing',
                     'u_unschedule': '? Scheduler Unscheduling',

                     'rp_overhead' : 'RP Overhead',
                     'rp_busy'     : 'Workload Execution',
                     'rp_idle'     : 'RP Idle',
                     'rp_orte'     : 'RP ORTE',
                     'rp_scheduler': 'RP Scheduler'
                    }

# there must be a better way to do this...
ORDERED_KEYS      = [
                     'p_boot',
                     'p_setup',
                     'p_orte',
                     'u_equeue',
                     'u_eprep',
                     'u_exec_rp',
                     'u_exec_cu',
                     'u_exec_orte',
                     'u_exec_app',
                     'u_unschedule',
                     'p_idle',
                     'p_term',
                     'p_agent',
                     ]

SUM_KEYS_1 = {'rp_scheduler' : ['u_equeue', 'u_unschedule'],
              'rp_orte'      : ['p_orte', 'u_exec_orte'],
              'rp_overhead'  : ['p_agent', 'p_boot', 'p_setup', 'p_term', 'u_eprep', 'u_exec_rp', 'u_exec_cu'],
              'rp_idle'      : ['p_idle'],
              'rp_busy'      : ['u_exec_app']
             }
ORDERED_KEYS_1 = ['rp_overhead', 'rp_scheduler', 'rp_orte', 'rp_busy', 'rp_idle']

SUM_KEYS_2 = {'rp_overhead'  : ['p_agent', 'p_boot', 'p_setup', 'p_orte', 'p_term', 'u_equeue', 'u_eprep', 'u_exec_rp', 'u_exec_cu', 'u_exec_orte', 'u_unschedule'],
              'rp_idle'      : ['p_idle'],
              'rp_busy'      : ['u_exec_app']
             }
ORDERED_KEYS_2 = ['rp_overhead', 'rp_busy', 'rp_idle']

# name the individual contributions (so, sans totals).  Also, `p_uexec` was
# meanwhile replaced by the different unit contributions + `p_idle`.  Also,
# we have a global `p_setup` now.
keys  = list(PILOT_DURATIONS.keys()) + list(UNIT_DURATIONS.keys()) + DERIVED_DURATIONS
keys  = [key for key in keys if 'total'    not in key]
keys  = [key for key in keys if 'p_uexec'  not in key]
keys  = [key for key in keys if 'p_setup_' not in key]

# make sure we can use the ORDERED set if needed.
assert(len(ORDERED_KEYS) == len(keys))

def update_ticks(x, pos):
    return int(x/4)

def get_utilization_durations(sources, version):

    if version != '2017':
        PILOT_DURATIONS['p_total'] = [{STATE: None,            EVENT: 'bootstrap_0_start'},
                                      {STATE: None,            EVENT: 'bootstrap_0_stop' }]
        PILOT_DURATIONS['p_boot']  = [{STATE: None,            EVENT: 'bootstrap_0_start'},
                                      {STATE: None,            EVENT: 'sync_rel'         }]
        PILOT_DURATIONS['p_term']  = [{STATE: None,            EVENT: 'cmd'              },
                                      {STATE: None,            EVENT: 'bootstrap_0_stop' }]

    utilization = dict() # dict of contributions to utilization
    data  = dict()       # the numbers we ultimately plot
    sids  = list()       # used for labels
    xkeys = list()       # x-axis labels

    # get the numbers we actually want to plot
    for src in sources:

        # always point to the tarballs
        if src[-4:] != '.tbz':
            src += '.tbz'

      # print
      # print '-----------------------------------------------------------'
        print(src)

        session = ra.Session(src, 'radical.pilot')
        pilots  = session.filter(etype='pilot', inplace=False)
        units   = session.filter(etype='unit',  inplace=True)
        sid     = session.uid
        sids.append(sid)

        if len(pilots.get()) > 1:
            raise ValueError('Cannot handle multiple pilots')

        # compute how many core-hours each duration consumed (or allocated,
        # wasted, etc - depending on the semantic type of duration)
        utilization[sid] = dict()

        for dname in PILOT_DURATIONS:
            utilization[sid][dname] = 0.0

        for dname in UNIT_DURATIONS:
            utilization[sid][dname] = 0.0

        # some additional durations we derive implicitly
        for dname in DERIVED_DURATIONS:
            utilization[sid][dname] = 0.0

        for pilot in pilots.get():

            # we immediately take of the agent nodes, and change pilot_size
            # accordingly
            cpn    = pilot.cfg.get('cores_per_node', 16)
            psize  = pilot.description['cores']
            anodes = 0
            for agent in pilot.cfg.get('agents', []):
                if pilot.cfg['agents'][agent].get('target') == 'node':
                    anodes += 1
            walltime   = pilot.duration(event=PILOT_DURATIONS['p_total'])
            psize_full = psize
            psize      = psize_full - anodes * cpn

            utilization[sid]['p_total'] += walltime * psize_full
            utilization[sid]['p_agent'] += walltime * anodes * cpn


            # now we can derive the utilization for all other pilot durations
            # specified.  Note that this is now off by some amount for the
            # bootstrapping step where we don't yet have sub-agents, but that
            # can be justified: the sub-agent nodes are explicitly reserved for
            # their purpose at that time. too.
            tot   = 0.0
            parts = 0.0
            for dname in PILOT_DURATIONS:
                if dname == 'p_total':
                    tot = pilot.duration(event=PILOT_DURATIONS[dname])
                    continue
                try:
                    dur = pilot.duration(event=PILOT_DURATIONS[dname])
                    parts += dur
                except Exception as e:
                    print('WARN: miss %s: %s' % (dname, e))
                    dur = 0.0
                    raise
                utilization[sid][dname] += dur * psize


        # we do the same for the unit durations - but here we add up the
        # contributions for all individual units.
        for unit in units.get():
            if version != '2017':
                unit.description['cores'] = unit.description['cpu_processes'] * unit.description['cpu_threads']
            usize  = unit.description['cores']
            uparts = 0.0
            utot   = 0.0
            for dname in UNIT_DURATIONS:
                dur = unit.duration(event=UNIT_DURATIONS[dname])
                utilization[sid][dname] += dur * usize
                if dname == 'u_total': utot   += dur
                else                 : uparts += dur

        # ----------------------------------------------------------------------
        #
        # sanity checks and derived values
        #
        # we add up 'p_setup_1' and 'p_setup_2' to 'p_setup'
        p_setup_1 = utilization[sid]['p_setup_1']
        p_setup_2 = utilization[sid]['p_setup_2']
        utilization[sid]['p_setup'] = p_setup_1 + p_setup_2
        del(utilization[sid]['p_setup_1'])
        del(utilization[sid]['p_setup_2'])

        # For both the pilot and the unit utilization, the
        # individual contributions must be the same as the total.
        parts  = 0.0
        tot    = utilization[sid]['p_total']

        for p in utilization[sid]:
            if p != 'p_total' and not p.startswith('u_'):
                parts += utilization[sid][p]
        assert(abs(tot - parts) < 0.0001), '%s == %s' % (tot, parts)

        # same for unit consistency
        parts  = 0.0
        tot    = utilization[sid]['u_total']
        for p in utilization[sid]:
            if p != 'u_total' and not p.startswith('p_'):
                parts += utilization[sid][p]

        # another sanity check: the pilot `p_uexec` utilization should always be
        # larger than the unit `total`.
        p_uexec = utilization[sid]['p_uexec']
        u_total = utilization[sid]['u_total']
        assert(p_uexec > u_total), '%s > %s' % (p_uexec, u_total)

        # We in fact know that the difference above, which is not explicitly
        # accounted for otherwise, is attributed to the agent component
        # overhead, and to the DB overhead: its the overhead to get from
        # a functional pilot to the first unit being scheduled, and from the
        # last unit being unscheduled to the pilot being terminated (witing for
        # other units to be finished etc).  We consider that time 'idle'
        utilization[sid]['p_idle' ] = p_uexec - u_total
        del(utilization[sid]['p_uexec'])

        xkeys.append('%s\n%s' % (len(units.get()), psize))

        # check that the utilzation contributions add up to the total
        tot_abs = utilization[sid]['p_total']
        sum_abs = 0
        sum_rel = 0
        for key in keys:
            if key not in data:
                data[key] = list()
            util_abs = utilization[sid][key]
            util_rel = 100.0 * util_abs / tot_abs
            sum_abs += util_abs
            sum_rel += util_rel

            if ABSOLUTE: data[key].append(util_abs)
            else       : data[key].append(util_rel)

    return data,sids,utilization,xkeys
