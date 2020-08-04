#!/usr/bin/env python3

import os
import sys
import time
import argparse

import multiprocessing as mp
# import pandas          as pd
# import numpy           as np

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
    def pre_exec(self):

        try:

            workload           = self._cfg.workload
            rank               = self._uid

            self._log.debug('pre_exec (%s)', workload.output)

          # receptor_file      = 'input_dir/receptorsV5.1/' + workload.receptor
            receptor_file      = 'input_dir/receptorsV6/'   + workload.receptor
            smiles_file        = 'input_dir/smiles/'        + workload.smiles
            output             = './out.'                   + workload.output

            self.verbose       = workload.verbose
            self.force_flipper = workload.force_flipper
            use_hybrid         = workload.use_hybrid
            high_resolution    = workload.high_resolution

            self.ofs           = oechem.oemolostream(output)
            self.ofs_lock      = mp.Lock()
            self.pdb_name      = self.get_root_protein_name(receptor_file)

            self._fin          = open(smiles_file, 'r')
            self.columns       = self._cfg.columns
            self.smiles_col    = self._cfg.smi_col
            self.name_col      = self._cfg.lig_col
            self.idxs          = self._cfg.idxs

            self.docker, _ = iface.get_receptor(receptor_file,
                                                use_hybrid=use_hybrid,
                                                high_resolution=high_resolution)

        except Exception:
            self._log.exception('pre_exec failed')
            raise


    # --------------------------------------------------------------------------
    #
    def get_data(self, off):

        self._fin.seek(off)
        line   = self._fin.readline()
      # ccount = line.count(',')  # FIXME: CVS parse on incorrect counts
        data   = line.split(',')
        return data


    # --------------------------------------------------------------------------
    #
    def dock(self, pos, off, uid):

        self._prof.prof('dock_start', uid=uid)

        # TODO: move smiles, ligand_name into args
        data        = self.get_data(off)
        smiles      = data[self._cfg.smi_col]
        ligand_name = data[self._cfg.lig_col]

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
            for i, col in enumerate(self._cfg.columns):
                if col.lower() != 'smiles':
                    value = data[i].strip()
                    if value and 'na' not in value.lower():
                        try:
                            oechem.OESetSDData(ligand, col, value)
                          # out.append([i, 'ok'])
                        except ValueError:
                          # out.append([i, 'err_value'])
                            pass
                    else:
                        pass
                      # out.append([i, 'no_value'])

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

