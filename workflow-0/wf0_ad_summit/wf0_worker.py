#!/usr/bin/env python3

import os
import sys
import glob
import time
import shutil

import multiprocessing as mp
# import pandas          as pd
# import numpy           as np

# from   openeye    import oechem
# from   impress_md import interface_functions as iface


import radical.pilot as rp
import radical.utils as ru


def _run_exec(data):
    d = 'bar'
    exec(data, globals(), locals())
    return d



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

        self._log.debug('started worker %s', self._uid)


    # --------------------------------------------------------------------------
    #
    def pre_exec(self):

        try:

            workload = self._cfg.workload

            self.cache    = workload.cache
            self.trivial  = workload.trivial

            self.smiles   = workload.smiles
            self.receptor = workload.receptor
            self.npts     = workload.args.npts
            self.center   = workload.args.center

            self.adt_util = os.environ['AUTODOCKTOOLS_UTIL']

            receptor_glob = 'input_dir/receptors.ad/%s*' % self.receptor
            smiles_file   = 'input_dir/smiles/%s.csv'    % self.smiles
            output        = './out.%s.sdf'               % self._uid


            # create and populate worker cache dir
            ru.rec_makedir(self.cache)
            shutil.copy(smiles_file, self.cache)

            for f in glob.glob(receptor_glob):
                shutil.copy(f, self.cache)

            # prepare to read smiles
            self._fin          = open('%s/%s.csv' % (self.cache, self.smiles), 'r')
            self.columns       = self._cfg.columns
            self.smiles_col    = self._cfg.smi_col
            self.name_col      = self._cfg.lig_col

            # all worker procs output the resulting SDF directly into the
            # result file residing on the shared FS - we lock that operation
            self.sdf_lock      = mp.Lock()


        except Exception:
            self._log.exception('pre_exec failed')
            raise


    # --------------------------------------------------------------------------
    #
    def post_exec(self):

        try:
            workload = self._cfg.workload

            self._log.debug('post_exec (%s)', workload.output)

            # FIXME: SDF concat per requested batch
            out, err, ret = ru.sh_callout("cp -r %s/results/ ." % self.cache)
            assert(not ret), [out, err, ret]


        except Exception:
            self._log.exception('post_exec failed')
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
    def dock(self, idxs, bid):

        ret = list()

        # create a cache dir per request
        bcache = '%s/%s' % (self.cache, bid)
        ru.rec_makedir(bcache)


        os.system('ls -la %s' % self.cache)
        os.system('ls -la %s' % bcache)

        # start new batch
        with open('%s/batch.%s' % (bcache, bid), 'w') as fin:
            fin.write('\n%s/%s.maps.fld\n\n' % (self.cache, self.cfg.receptor))

        for idx, pos, off in idxs:
            self.prepare_ligands(idx, pos, off, bid, bcache)

        self.prepare_grids(bid, bcache)
        self.run_autodock_gpu(bid, bcache)

        for idx, pos, off in idxs:
            self.transform_results(idx, pos, off, bid, bcache)
            ret.append('foo')

        return ret


    # --------------------------------------------------------------------------
    #
    def prepare_ligands(self, idx, pos, off, bid, bcache):

        self._prof.prof('dock_start', uid=idx)

        # TODO: move smiles, ligand_name into args
        data        = self.get_data(off)
        smiles      = data[self._cfg.smi_col]
        ligand_name = data[self._cfg.lig_col]

        # obtain unbound fragment
        fragments = [ion for ion in smiles.split('.')
                         if  ion not in self.trivial]
        assert(fragments          ), ("Empty SMILES after deleting trivial ions")
        assert(len(fragments) == 1), ("SMILES contains multiple non-bonded fragments")
        fragment = fragments[0]
       
        babel = 'obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2'
        out, err, ret = ru.sh_callout('echo "%s" | %s > %s/%s.mol2'
                                     % (fragment, babel, bcache, idx), shell=True)
        assert(not ret), [out, err, ret]

        cmd = '%s/prepare_ligand4.py -l %s/%s.mol2 -F -o %s/%s.pdbqt -d %s/ligand_dict.py' \
              % (self.adt_util, bcache, idx, bcache, idx, bcache)
        out, err, ret = ru.sh_callout('pythonsh %s' % cmd)
        assert(not ret), [out, err, ret]

        out, err, ret = ru.sh_callout('cat %s/%s.pdbqt >> %s/batch.%s'
                                     % (bcache, idx, bcache, bid), shell=True)
        assert(not ret), [out, err, ret]

        out, err, ret = ru.sh_callout('echo "%s" >> %s/batch.%s'
                                     % (idx, bcache, bid), shell=True)
        assert(not ret), [out, err, ret]


    # --------------------------------------------------------------------------
    #
    def prepare_grids(self, bid, bcache):

        # exec(open('%s/ligand_dict.py' % bcache).read())
        #
        # Oh boy, don't we all love Python?  It is a language with
        # *unparalleled* flexibility, ease of use, and low learning curve which
        # guarantees success after only a few days of headscratching - nice!
        #
        # `exec` executes a given string in the current interpreter context,
        # using current set `locals()` and `globals()`.  Well, kind of - because
        # the current interpreter context might have optimized those away.  For
        # `exec` it will make an exception though, and disabling that
        # optimization.  Which is great, so `exec` can work, which is nice.
        # Performance?  Yeah, we are using PYTHON in case you didn't notice, so
        # LOL.
        #
        # The interpreter also turns optimization off in other cases.  Like, if
        # you have sub-methods.  Or class methods.  Which is ok.  ONLY IT TURNS
        # OPTIMIZATION OFF IN A DIFFERENT WAY!  Because, LOL.  Or something.
        #
        # Anyways, don't use `exec` in methods with methods or in classes.  Or
        # in files which define classes and methods.  Or whatever - didn't
        # bother tracking down why it's not working here specifically, so we use
        # an external helper.
        #
        # LOL
        #
        os.system('python3 ./read_ligand_dict.py %s ' % bcache)
        d = ru.read_json('%s/ligand_dict.json' % bcache)

        atom_types = set()
        for val in d.values():
            atom_types.update(val["atom_types"])

        ligand_types = ','.join(list(atom_types))

        cmd = '%s/prepare_gpf4.py  -r %s/%s.pdbqt -p ligand_types="%s" -p npts="%s" -p gridcenter="%s" -o %s.gpf' \
                % (self.adt_util, self.cache, self.receptor, ligand_types, 
                        self.npts, self.center, self.receptor)
        out, err, ret = ru.sh_callout('pythonsh %s' % cmd)
        assert(not ret), [out, err, ret]

        # FIXME: use python shell utils
        # FIXME: autogrid needs that file in $PWD.  Is a link ok?
        out, err, ret = ru.sh_callout("ln -s %s/%s.pdbqt ."
                                      % (self.cache, self.receptor))
        assert(not ret), [out, err, ret]
        os.system('echo bcache %s' % bcache)
        os.system('ls -la %s' % bcache)

      # out, err, ret = ru.sh_callout('autogrid4 -p %s.gpf -l %s.glg'
      #                             % (self.receptor, self.receptor))
      # assert(not ret), [out, err, ret]


    # --------------------------------------------------------------------------
    #
    def run_autodock_gpu(self, bid, bcache):
        
        # FIXME: GPU_ID
        gpu_id = 1
        cmd = 'autodock_gpu_64wi -filelist %s/batch.%s -devnum %s -lsmet "ad"' \
              % (bcache, bid, gpu_id)
        print(cmd)
        time.sleep(5)
      # out, err, ret = ru.sh_callout(cmd)
      # assert(not ret), [out, err, ret]
        
        
    # --------------------------------------------------------------------------
    #
    def transform_results(self, idx, pos, off, bid, bcache):

        print('writing to %s.sdf' % bid)
        with open('%s.sdf' % bid, 'a+') as fout:
            fout.write('result for %s %s %s %s\n' % (bid, idx, pos, off))
        return

        data        = self.get_data(off)
        smiles      = data[self._cfg.smi_col]

        cmd = '$AUTODOCKTOOLS_UTIL/write_lowest_energy_ligand.py -f %s.dlg -o %s_tmp.pdbqt' % (bid, bid)
        out, err, ret = ru.sh_callout('pythonsh %s' % cmd)
        assert(not ret), [out, err, ret]

        cmd = 'obabel -ipdbqt %s_tmp.pdbqt -osdf | head -n -1 > %s.sdf' % (bid, bid)
        out, err, ret = ru.sh_callout(cmd, shell=True)
        assert(not ret), [out, err, ret]

        if os.path.isfile('%s.sdf' % bid):

            score = None
            with open('%s.dlg' % bid, 'r') as fin:

                for line in fin.readlines:
                    if 'USER    Estimated Free Energy of Binding    =' in line:
                        if 'DOCKED: USER' not in line:
                            score = line.split()[7]
                            break

            assert(score is not None)

            with open('%s.sdf' % bid, 'a') as fout:
                fout.write('>  <AutodockScore>\n%s\n\n>  <TITLE>\n%s\n\n$$$$\n' % idx)

            # FIXME: write in-place 
          # mv $id.sdf ../results


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    # the `info` dict is passed to the worker as config file.
    # Create the worker class and run it's work loop.
    worker = MyWorker(sys.argv[1])
    worker.run()


# ------------------------------------------------------------------------------

