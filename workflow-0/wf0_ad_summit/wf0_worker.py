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

pid  = os.getpid()
rank = int(os.environ.get('PMIX_RANK', -1))

def out(data):
    sys.stdout.write('==== %2d  %8d  %12d  %s\n' % (rank, pid, time.time(), data))
    sys.stdout.flush()



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

        with open('./env.%d' % os.getpid(), 'w') as fout:
            for k in sorted(os.environ.keys()):
                v = os.environ[k]
                fout.write('%s=%s\n' % (k, v))

        rp.task_overlay.Worker.__init__(self, cfg)

        self.register_call('dock', self.dock)

        self._log.debug('started worker %s', self._uid)


    # --------------------------------------------------------------------------
    #
    def pre_exec(self):

        try:

            workload = self._cfg.workload

            self.sbox     = os.getcwd()
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
            self._log.debug('post_exec')

        except Exception:
            self._log.exception('post_exec failed')
            raise


    # --------------------------------------------------------------------------
    #
    def get_data(self, off):

        self._fin.seek(off)
        line   = self._fin.readline()
      # ccount = line.count(',')  # FIXME: CVS parse on incorrect counts
        data   = [x.strip() for x in line.split(',')]
        return data


    # --------------------------------------------------------------------------
    #
    def bak(self, bid, name):

        os.system('cp -r %s/%s %s/%s.%s' %(self.cache, bid, self.sbox, bid, name))


    # --------------------------------------------------------------------------
    #
    def dock(self, idxs, bid):

        ret = list()

        # create a cache dir per request
        bcache = '%s/%s' % (self.cache, bid)
        ru.rec_makedir(bcache)

        # we change into the cachdir, to simplify paths and to ensure that
        # autodock tmp files also end up here (and not in the worker sbox on the
        # chared fs)
        os.chdir(bcache)

        # start new batch
        with open('./batch', 'w') as fout:
            fout.write('\n%s/%s.maps.fld\n\n' % (self.cache, self.receptor))

            for idx, pos, off in idxs:
                # TODO: cache for result loop below
                data = self.get_data(off)
                smi  = data[self._cfg.smi_col]
                lig  = data[self._cfg.lig_col]

                print('%s : %s : %s : %s' % (self.uid, bid, lig, smi))
                self.prepare_ligands(idx, pos, off, smi, lig, bid, batch=fout)

        self.prepare_grids(bid)
        self.run_autodock_gpu(bid)

        with open('./%s.sdf' % (bid), 'w') as fout:
            for idx, pos, off in idxs:
                # TODO: cache from prep loop below
                data = self.get_data(off)
                smi  = data[self._cfg.smi_col]
                lig  = data[self._cfg.lig_col]

                score = self.transform_results(idx, pos, off, smi, lig, bid, sdf=fout)
                ret.append(score)

        with self.sdf_lock:
            cmd = 'cat ./%s.sdf >> %s/%s.sdf' % (bid, self.sbox, self.uid)
            out, err, ret = ru.sh_callout(cmd, shell=True)
            assert(not ret), [cmd, out, err, ret]

        self.bak(bid, 'final')

        return ret


    # --------------------------------------------------------------------------
    #
    def prepare_ligands(self, idx, pos, off, smi, lig, bid, batch):

        self._prof.prof('dock_start', uid=idx)

        # obtain unbound fragment
        fragments = [ion for ion in smi.split('.')
                         if  ion not in self.trivial]
        assert(fragments          ), ("Empty SMILES after deleting trivial ions")
        assert(len(fragments) == 1), ("SMILES contains multiple non-bonded fragments")
        fragment = fragments[0]
       
        babel = 'obabel -h --gen3d --conformer --nconf 100 --score energy -ismi -omol2'
        cmd   = 'echo "%s" | %s > ./%s.mol2' % (fragment, babel, lig)
        out, err, ret = ru.sh_callout(cmd, shell=True)
        assert(not ret), [cmd, out, err, ret]

        cmd = 'pythonsh %s/prepare_ligand4.py -l ./%s.mol2 -F -o ./%s.pdbqt -d ./ligand_dict.py' \
              % (self.adt_util, lig, lig)
        out, err, ret = ru.sh_callout(cmd)
        assert(not ret), [cmd, out, err, ret]

        batch.write('./%s.pdbqt\n%s\n' % (lig, lig))


    # --------------------------------------------------------------------------
    #
    def prepare_grids(self, bid):

        # exec(open('./ligand_dict.py').read())
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
        os.system('python3 %s/read_ligand_dict.py' % self.sbox)
        d = ru.read_json('./ligand_dict.json')

        atom_types = set()
        for val in d.values():
            atom_types.update(val["atom_types"])

        ligand_types = ','.join(list(atom_types))

        cmd = '%s/prepare_gpf4.py  -r %s/%s.pdbqt -p ligand_types="%s" -p npts="%s" -p gridcenter="%s" -o %s.gpf' \
                % (self.adt_util, self.cache, self.receptor, ligand_types, 
                        self.npts, self.center, self.receptor)
        out, err, ret = ru.sh_callout('pythonsh %s' % cmd)
        assert(not ret), [cmd, out, err, ret]

        # FIXME: use python shell utils
        # FIXME: autogrid needs that file in $PWD.  Is a link ok?
        cmd = "ln -s %s/%s.pdbqt ." % (self.cache, self.receptor)
        out, err, ret = ru.sh_callout(cmd)
        assert(not ret), [cmd, out, err, ret]

        cmd = 'autogrid4 -p %s.gpf -l %s.glg' % (self.receptor, self.receptor)
        out, err, ret = ru.sh_callout(cmd)
        assert(not ret), [cmd, out, err, ret]


    # --------------------------------------------------------------------------
    #
    def run_autodock_gpu(self, bid):
        
        # FIXME: GPU_ID
        gpu_id = os.environ.get('CUDA_VISIBLE_DEVICES')

        # autodock GPU IDs start at 1
        if gpu_id: gpu_id = int(gpu_id) + 1
        else     : gpu_id = 1

        os.environ['WF0_HOME'] = self.sbox
        print('using gpu %d' %  gpu_id)
      # exe = 'autodock_gpu_64wi'
        exe = 'autodock_gpu_64wi_debug'
        cmd = '%s -filelist ./batch -devnum %s -lsmet "ad"' % (exe, gpu_id)

        self.bak(bid, 'ad')
        self._log.debug('=== %s', cmd)
        out, err, ret = ru.sh_callout(cmd)
        assert(not ret), [cmd, out, err, ret]
        
        
    # --------------------------------------------------------------------------
    #
    def transform_results(self, idx, pos, off, smi, lig, bid, sdf):

        if not os.path.isfile('%s.dlg' % lig):
            print('no dlg for %s' % lig)
            return None

        os.environ['WF0_HOME'] = self.sbox
        cmd = '%s/write_lowest_energy_ligand.py -f %s.dlg -o %s_tmp.pdbqt' \
                % (self.adt_util, lig, lig)
        out, err, ret = ru.sh_callout('pythonsh %s' % cmd)
        assert(not ret), [cmd, out, err, ret]

        cmd = 'obabel -ipdbqt %s_tmp.pdbqt -osdf | head -n -1' % lig
        out, err, ret = ru.sh_callout(cmd, shell=True)
        assert(not ret), [cmd, out, err, ret]
        babel_output = out

        if not babel_output:
            print("no babel output")
            return None

        score = None
        with open('%s.dlg' % lig, 'r') as fin:

            for line in fin.readlines():
                if 'USER    Estimated Free Energy of Binding    =' in line:
                  # if 'DOCKED: USER' not in line:
                    if True:
                        print('score line: %s' % line)
                        score = line.split()[8]
                        break
        print('==== %s score: %s' % ('%s.dlg' % lig, score))

      # assert(score is not None)

        sdf.write('%s\n>  <AutodockScore>\n%s\n\n>  <TITLE>\n%s\n\n$$$$\n'
                  % (babel_output, score, lig))

        return score

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

