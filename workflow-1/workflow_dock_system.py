#!/usr/bin/env python3

import os
import sys
import pprint

import pandas        as pd
import radical.utils as ru

from impress_md import interface_functions as iface


# --------------------------------------------------------------------------
#
def docking(pos, smiles, path_input, path, dbase_name, target_name, docker, write,
            recept, receptor_file, name, docking_only):
    print('=== docking_A', pos)
    # or iface.RunDocking_A
    try:
        score, res = iface.RunDocking_(smiles, path_input, path, dbase_name,
                                       target_name, dock_obj=docker,
                                       write=write, recept=recept,
                                       receptor_file=receptor_file, name=name,
                                       docking_only=docking_only)
        res = res.strip()
        print('=== docking_A', score, res)
        return score, res
    except Exception as e:
        print('=== docking_A FAILED: ', str(e))
        return False, False


def parameterize(pos, path):
    print('=== parameterize', pos)
    try:
        iface.ParameterizeOE(path)
        print('=== parameterize True')
        return True
    except Exception as e:
        print('=== parameterize FAILED: ', str(e))
        return False


def minimization(pos, path, write, gpu):
    print('=== mimnimization', pos)
    try:
        mscore = iface.RunMinimization_(path, path, write=write, gpu=gpu)
        print('=== mimnimization', mscore)
        return mscore
    except Exception as e:
        print('=== mimnimization FAILED: ', str(e))
        return False


def mmgbsa(pos, path, gpu, niters):
    print('=== mmgbsa', pos)
    try:
        escore = iface.RunMMGBSA_(path, path, gpu=True)  # niters=niters)
        print('=== mmgbsa', escore)
        return escore
    except Exception as e:
        print('=== mmgbsa FAILED: ', str(e))
        return False


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    smiles_file   = sys.argv[1]
    receptor_file = sys.argv[2]
    target_name   = receptor_file
    dbase_name    = 'ena_db'
    path_root     = 'rank'
    path_output   = 'output/'
    path_input    = 'input/'
    state         = dict()

    smiles_data   = pd.read_csv(smiles_file, sep=' ', header=None)

    rec_base      = os.path.basename(receptor_file).split('.')[0]
    smi_base      = os.path.basename(smiles_file  ).split('.')[0]
    print(rec_base)

    state_file    = '%s_%s.json' % (rec_base, smi_base)

    if not os.path.exists(path_output):
        os.mkdir(path_output)

    if os.path.exists(state_file):
        state = ru.read_json(state_file)

    def pstate_flush(_state):
        ru.write_json(_state, '%s.new' % state_file)
        os.system('mv %s.new %s' % (state_file, state_file))


    def pstate_get(_state, pos, key):
        pos = str(pos)
        if pos not in _state:
            _state[pos] = {'docking'      : [None, None],  # core, res
                           'parameterize' : None,
                           'minimization' : None,
                           'mmgbsa'       : None,
                           'result'       : None}
        return _state[pos][key]


    def pstate_set(_state, pos, key, val, flush=False):
        pos = str(pos)
        _state[pos][key] = val
        if flush:
            pstate_flush(_state)


    docker, recept = iface.get_receptr(receptor_file=receptor_file)
    print('=== init')

    for pos in range(smiles_data.shape[0]):

        smiles = smiles_data.iloc[pos, 0]
        name   = smiles_data.iloc[pos, 1]
        path   = path_root + str(pos) + "/"

        score, res = pstate_get(state, pos, 'docking')
        if score is None and res is None:
            score, res = docking(pos, smiles, path_input, path,
                                 dbase_name, target_name, docker,
                                 write=True, recept=recept,
                                 receptor_file=receptor_file, name=name,
                                 docking_only=True)
            pstate_set(state, pos, 'docking', [score, res])
            if score is False and res is False:
                pstate_set(state, pos, 'parameterize', False)
                pstate_set(state, pos, 'minimization', False)
                pstate_set(state, pos, 'mmgbsa',       False)
                pstate_set(state, pos, 'result',       False)
                pstate_flush(state)

        param = pstate_get(state, pos, 'parameterize')
        if param is None:
            param = parameterize(pos, path)
            pstate_set(state, pos, 'parameterize', param)
            if param is False:
                pstate_set(state, pos, 'minimization', False)
                pstate_set(state, pos, 'mmgbsa',       False)
                pstate_set(state, pos, 'result',       False)
                pstate_flush(state)

        mscore = pstate_get(state, pos, 'minimization')
        if mscore is None:
            mscore = minimization(pos, path, write=True, gpu=True)
            pstate_set(state, pos, 'minimization', mscore)
            if mscore is False or mscore < 500:
                pstate_set(state, pos, 'mmgbsa', False)
                pstate_set(state, pos, 'result', False)
                pstate_flush(state)

        escore = pstate_get(state, pos, 'mmgbsa')
        if escore is None:
            escore = mmgbsa(pos, path, gpu=True, niters=5000)  # 5ns
            pstate_set(state, pos, 'mmgbsa', escore)
            if escore is False:
                pstate_set(state, pos, 'result', False)
                pstate_flush(state)

        result = pstate_get(state, pos, 'result')
        if result is None:
            with open(path + "/metrics.csv") as f:
                next(f)
                result = next(f)
            pstate_set(state, pos, 'result', result)
            pstate_flush(state)

      # pprint.pprint(state)


# ------------------------------------------------------------------------------

