#!/usr/bin/env python3

import os
import sys
import time


import argparse
import os

import multiprocessing as mp
import pandas          as pd
import numpy           as np

from   openeye    import oechem
from   impress_md import interface_functions as iface


import radical.pilot as rp


# ------------------------------------------------------------------------------
#
class MyWorker(rp.task_overlay.Worker):
    '''
    This class provides the required functionality to execute work requests.
    In this simple example, the worker only implements a single call: `dock`.
    '''


    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg):

        rp.task_overlay.Worker.__init__(self, cfg)

        self.register_call('dock', self.dock)


    # --------------------------------------------------------------------------
    #
    def get_root_protein_name(self, file_name):

        return file_name.split("/")[-1].split(".")[0]


    # --------------------------------------------------------------------------
    #
    def get_smiles_col(self, col_names):

        print(col_names)
        return int(np.where(['smile' in s.lower() for s in col_names])[0][0])


    # --------------------------------------------------------------------------
    #
    def get_ligand_name_col(self, col_names):

        return int(np.where(['id'    in s.lower() or
                             'title' in s.lower() or
                             "name"  in s.lower()
                             for s in col_names])[0][0])


    # --------------------------------------------------------------------------
    #
    def pre_exec(self):

        try:
            self._log.debug('pre_exec')

            workload          = self._cfg.workload
            rank              = self._uid

            localf            = workload.localf
            target_file       = 'input_dir/' + workload.receptor
            smiles_file       = 'input_dir/' + workload.smiles
            sdf               = workload.sdf

            basename          = ".".join(sdf.split(".")[:-1])
            file_ending       =          sdf.split(".")[ -1]
            output_poses      = basename + "_" + str(rank) + "." + file_ending

            # setting don't change
            use_hybrid      = True
            high_resolution = True

            # set logging if used
            if localf:
                localf += "tmp_" + str(rank) + ".sdf"
                self.ofs = oechem.oemolostream(localf)
                print('1', self.ofs)
            else:
                self.ofs = oechem.oemolostream(output_poses)

            self.ofs_lock      = mp.Lock()
            self.pdb_name      = self.get_root_protein_name(target_file)
            self.smiles_file   = pd.read_csv(smiles_file)
            self.columns       = self.smiles_file.columns.tolist()
            self.smiles_col    = self.get_smiles_col(self.columns)
            self.name_col      = self.get_ligand_name_col(self.columns)
            self.force_flipper = workload.force_flipper
            self.verbose       = workload.verbose

            self.docker, _ = iface.get_receptor(target_file, use_hybrid=use_hybrid,
                                                high_resolution=high_resolution)

        except Exception:
            self._log.exception('pre_exec failed')
            raise


    # --------------------------------------------------------------------------
    #
    def dock(self, pos, uid):

        self._prof.prof('dock_start', uid=uid)

        # TODO: move smiles, ligand_name into args
        smiles             = self.smiles_file.iloc[pos, self.smiles_col]
        ligand_name        = self.smiles_file.iloc[pos, self.name_col]
        score, res, ligand = iface.RunDocking_(smiles,
                                               dock_obj=self.docker,
                                               pos=pos,
                                               name=ligand_name,
                                               target_name=self.pdb_name,
                                               force_flipper=self.force_flipper)

      # if self.verbose:
      #     print("RANK {}:".format(rank), res, end='')

        out = list()
        if self.ofs and ligand is not None:
            for i, col in enumerate(self.columns):
                value = str(self.smiles_file.iloc[pos, i]).strip()
                if col.lower() != 'smiles'  and \
                  'na' not in value.lower() and \
                   len(value) > 1:
                    try:
                        oechem.OESetSDData(ligand, col, value)
                        out.append([i, 'ok'])
                    except ValueError:
                        out.append([i, 'value error'])
                        pass

            self._prof.prof('dock_io_start', uid=uid)
            with self.ofs_lock:
                oechem.OEWriteMolecule(self.ofs, ligand)
            self._prof.prof('dock_io_stop', uid=uid)
        else:
            out.append([None, 'skip'])

      # self._log.debug(out)
        self._prof.prof('dock_stop', uid=uid)
        return out


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # the `info` dict is passed to the worker as config file.
    # Create the worker class and run it's work loop.
    worker = MyWorker(sys.argv[1])
    worker.run()


# ------------------------------------------------------------------------------

