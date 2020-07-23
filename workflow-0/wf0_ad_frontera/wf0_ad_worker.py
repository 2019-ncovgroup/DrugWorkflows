#!/usr/bin/env python3

import os
import sys
import time
import argparse

import subprocess      as sp
import multiprocessing as mp
# import pandas          as pd
# import numpy           as np

# from   openeye    import oechem
# from   impress_md import interface_functions as iface


import radical.pilot as rp
import radical.utils as ru


# ------------------------------------------------------------------------------
#
class MyWorker(rp.task_overlay.Worker):
    '''
    This class provides the required functionality to execute work requests.
    In this simple example, the worker only implements a single call: `autodock`.
    '''

    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg):

        rp.task_overlay.Worker.__init__(self, cfg)

        self.register_call('autodock', self.autodock)


    # --------------------------------------------------------------------------
    #
    def get_root_protein_name(self, file_name):

        return file_name.split("/")[-1].split(".")[0]


    # --------------------------------------------------------------------------
    #
    def pre_exec(self):

        self._log.debug('=== pre_exec')

        try:

            workload           = self._cfg.workload
            rank               = self._uid

            self._log.debug('pre_exec (%s)', workload.output)

            receptor_file      = 'input_dir/receptorsV5.1/%s' % workload.receptor
            smiles_file        = 'input_dir/%s.csv'           % workload.smiles
            output             = './out.%s'                   % workload.output

            self.verbose       = workload.verbose
            self.force_flipper = workload.force_flipper
            use_hybrid         = workload.use_hybrid
            high_resolution    = workload.high_resolution

            # prepare the smiles file for search and read
            self._fin          = open(smiles_file, 'r')
            self.columns       = self._cfg.columns
            self.smiles_col    = self._cfg.smi_col
            self.name_col      = self._cfg.lig_col
            self.idxs          = self._cfg.idxs

            # prepare autodocktool scripts for calling in-proc
            home   = os.environ['HOME']
            path1  = '/tmp/tools/DataCrunching/ProcessingScripts/Autodock'
            path2  = '/tmp/tools/MGLToolsPckgs/AutoDockTools/Utilities24'
            self.ad_funcs      = {
                'echo_smiles'    : ru.which('%s/echo_smiles.py'                % path1),
                'prepare_ligand4': ru.which('%s/prepare_ligand4.py'            % path2),
                'prepare_gpf4'   : ru.which('%s/prepare_gpf4.py'               % path2),
                'prepare_dpf42'  : ru.which('%s/prepare_dpf42.py'              % path2),
                'write_ligand'   : ru.which('%s/write_lowest_energy_ligand.py' % path2),
            }

            # locate autodocktool binaries for calling
            self.ad_bins       = {
                'autogrid4'   : ru.which('autogrid4'),
                'autodock4'   : ru.which('autodock4'),
                'obabel'      : ru.which('obabel')
            }


        except Exception:
            self._log.exception('pre_exec failed')
            raise

        self._log.debug('=== pre_exec ok')


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
    def prepare_task(self, task):

        self._log.debug('==== 2 prep 1')

        pos    = task['data']['kwargs']['pos']
        off    = task['data']['kwargs']['off']
        data   = self.get_data(off)
        smiles = data[self._cfg.smi_col]

        # $path/echo_smiles.py "$smiles" \
        # | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2 \
        # > $id.mol2
        self._log.debug('==== 2 prep 2')
        cmd2  = "./wf0_ad_helper_1.sh %s \"%s\"" % (pos, smiles)
        out2, err2, ret2 = ru.sh_callout(cmd2)
        self._log.debug('==== 2 %s', cmd2)
        self._log.debug('===  2 %s\nout: %s\nerr: %s', ret2, out2, err2)

        self._log.debug('==== 2 prep 3')
        assert(not ret2), err2



    # --------------------------------------------------------------------------
    #
    def autodock(self, uid, pos, off, protein, center, points, residues=None):

        orig  = os.getcwd()
        pwd   = '/tmp/sbox_%s' % pos

        os.chdir(pwd)
        os.system('ln -s /%s/%s* .' % (orig, protein))

        self._log.debug('=== 0 %s (%s)', pos, pwd)

        # This script takes 6 argument:
        #
        # - protein  : protein              : pdbqt-str
        # - smiles   : SMILES string        : str
        # - smiles_id: smiles identifier    : str
        # - center   : pocket center        : 3-tuple (xcoord,ycoord,zcoord)
        # - points   : number grid points   : 3-tuple (nptsx,nptsy,nptsz)
        # - residues : flexible residues    : pdb-str, optional
        #

        data        = self.get_data(off)
        smiles      = data[self._cfg.smi_col]

        sid         = pos
        results     = '%s/../' % orig  # master sandbox
        sdf         = '%s/%s.sdf' % (results, sid)

        pythonsh    = '/tmp/tools/bin/pythonsh'

        if os.path.isfile(sdf):
            # we have this result already so skip
            return 'EXISTS'

        # FIXME: constant - stage
      # cp $protein.pdbqt .     # TODO AM: why?  Does a link work?
      # cp $residues.pdb  .     # TODO AM: same

      # # $path/echo_smiles.py "$smiles" \
      # # | obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2 \
      # # > $id.mol2
      # cmd2  = "sh -c './wf0_ad_helper_1.sh %s \"%s\" > %s.mol2'" % (sid, smiles, sid)
      # out2, err2, ret2 = ru.sh_callout(cmd2)
      # self._log.debug('==== 2 %s', cmd2)
      # self._log.debug('===  2 %s\nout: %s\nerr: %s', ret2, out2, err2)
      # assert(not ret2), err2

        # prepare_ligand4.py -l $id.mol2 -F -o $id.pdbqt
        args3 = '-l %s.mol2 -F -o %s.pdbqt' % (sid, sid)
        cmd3  = '%s %s %s' % (pythonsh, self.ad_funcs['prepare_ligand4'], args3)
        out3, err3, ret3 = ru.sh_callout(cmd3)
        self._log.debug('==== 3 %s', cmd3)
        self._log.debug('===  3 %s\n%s\n%s', ret3, out3, err3)
        assert(not ret3), err3


        # prepare_gpf4.py  -l $id.pdbqt -r $1.pdbqt -p npts="$4" -p gridcenter="$3" -o $id.gpf
        # prepare_gpf4.py  -l $id.pdbqt -r $1.pdbqt -p npts="$4" -p gridcenter="$3" -o $id.gpf -x $5.pdb
        args4 = '-l %s.pdbqt -r %s.pdbqt -p npts=%s -p gridcenter=%s -o %s.gpf' \
              % (sid, protein, points, center, sid)
        if residues:
            args4 += ' -x %s.pdb' % residues
        cmd4 = '%s %s %s' % (pythonsh, self.ad_funcs['prepare_gpf4'], args4)
        out4, err4, ret4 = ru.sh_callout(cmd4)
        self._log.debug('==== 4 %s', cmd4)
        self._log.debug('===  4 %s\nout: %s\nerr: %s', ret4, out4, err4)
        assert(not ret4), err4


        # prepare_dpf42.py -l $id.pdbqt -r $1.pdbqt -p ga_run=20 -o $id.dpf
        # prepare_dpf42.py -l $id.pdbqt -r $1.pdbqt -p ga_run=20 -o $id.dpf -x $5.pdb
        args5 = '-l %s.pdbqt -r %s.pdbqt -p ga_run=20 -o %s.dpf' \
                % (sid, protein, sid)
        if residues:
            args4 += ' -x %s.pdb' % residues
        cmd5 = '%s %s %s' % (pythonsh, self.ad_funcs['prepare_dpf42'], args5)
        out5, err5, ret5 = ru.sh_callout(cmd5)
        self._log.debug('==== 5 %s', cmd5)
        self._log.debug('===  5 %s\nout: %s\nerr: %s', ret5, out5, err5)
        assert(not ret5), err5


        # autogrid4 -p $id.gpf -l $id.glg
        cmd6 = 'autogrid4 -p %s.gpf -l %s.glg' % (sid, sid)
        out6, err6, ret6 = ru.sh_callout(cmd6)
        self._log.debug('==== 6 %s', cmd6)
        self._log.debug('===  6 %s\nout: %s\nerr: %s', ret6, out6, err6)
        assert(not ret6), err6


        # autodock4 -p $id.dpf -l $id.dlg
        cmd7 = 'autodock4 -p %s.dpf -l %s.dlg' % (sid, sid)
        out7, err7, ret7 = ru.sh_callout(cmd7)
        self._log.debug('==== 7 %s', cmd7)
        self._log.debug('===  7 %s\nout: %s\nerr: %s', ret7, out7, err7)
        assert(not ret7), err7

        # pythonsh write_lowest_energy_ligand.py
        args8 = '-f %s.dlg -o %s_tmp.pdbqt' % (sid, sid)
        cmd8  = '%s %s %s' % (pythonsh, self.ad_funcs['write_ligand'], args8)
        out8, err8, ret8 = ru.sh_callout(cmd8)
        self._log.debug('==== 8 %s', cmd8)
        self._log.debug('===  8 %s\nout: %s\nerr: %s', ret8, out8, err8)
        assert(not ret8), err8

        # obabel -ipdbqt ${id}_tmp.pdbqt -osdf | head --lines=-1 > $id.sdf
        cmd9 = 'obabel -ipdbqt %s_tmp.pdbqt -osdf | head -n -1 > %s' % (sid, sdf)
        out9, err9, ret9 = ru.sh_callout(cmd9, shell=True)
        self._log.debug('==== 9 %s', cmd9)
        self._log.debug('===  9 %s\nout: %s\nerr: %s', ret9, out9, err9)
        assert(not ret9)


        cmd10 = ('echo ">  <AutodockScore>" >> %s' % sdf
             +  ' ; grep "USER    Estimated Free Energy of Binding    =" %s.dlg' % sid
             +  ' | grep -v "DOCKED: USER"'
             +  ' | head --lines=1'
             +  ' | awk "{print $8}" >> %s' % sdf
             +  ' ; printf "\n>  <TITLE>\n%s\n\n$$$$\n" >> %s' % (sid, sdf)
        )
        out10, err10, ret10 = ru.sh_callout(cmd10, shell=True)
        self._log.debug('==== 10 %s', cmd10)
        self._log.debug('===  10 %s\nout: %s\nerr: %s', ret10, out10, err10)
        assert(not ret10)

        self._prof.prof('dock_stop', uid=uid)
        return 'OK'


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # the `info` dict is passed to the worker as config file.
    # Create the worker class and run it's work loop.
    worker = MyWorker(sys.argv[1])
    worker.run()
    print('=== DONE')


# ------------------------------------------------------------------------------

