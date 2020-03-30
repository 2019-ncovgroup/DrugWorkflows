from radical import entk
import os
import argparse, sys

class ESMACS(object):

    def __init__(self):
        self.set_argparse()
        self._set_rmq()
        self.am = entk.AppManager(hostname=self.rmq_hostname, port=self.rmq_port)
        self.p = entk.Pipeline()
        self.s = entk.Stage()


    def _set_rmq(self):
        self.rmq_port = int(os.environ.get('RMQ_PORT', 5672))
        self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', 'localhost')


    def set_resource(self, res_desc):
        res_desc["schema"] = "local"
        self.am.resource_desc = res_desc


    def set_argparse(self):
        parser = argparse.ArgumentParser(description="ESMACS")
        parser.add_argument("--task", "-t", help="esmacs or sim")
        args = parser.parse_args()
        self.args = args
        if args.task is None:
            parser.print_help()
            sys.exit(-1)


    def raw_submission_esmacs_sh(self, rep_count=24):#mmpbsa(self):


        for i in range(1, rep_count + 1):
            t = entk.Task()
            t.pre_exec = [ 
                    "export OMP_NUM_THREADS=1",
                    "module load cuda/10.1.243 gcc/6.4.0",
                    "module load spectrum-mpi/10.3.1.2-20200121",
                    "export CUDA_HOME=/sw/summit/cuda/10.1.243",
                    "export INPATH=\"$MEMBERWORK/chm155/inpath\"", # TODO: parameterized
                    "source /gpfs/alpine/scratch/apbhati/chm155/AmberTools19/amber18/amber.sh", #TODO: parameterized
                    "export LD_LIBRARY_PATH=\"/sw/summit/cuda/10.1.243/lib:${LD_LIBRARY_PATH}\"",
                    "cd $INPATH",
                    "export OUTPATH=\"$INPATH/rep{}".format(i),
                    "cd $OUTPATH" 
                    ]
            t.executable = "MMPBSA.py.MPI"
            t.arguments = ("-O -i $INPATH/mmpbsa.in -sp " + \
                    "$INPATH/complex.prmtop -cp $INPATH/com.prmtop -rp " + \
                    "$INPATH/apo.prmtop -lp $INPATH/lig.prmtop -y traj.dcd " + \
                    "> mmpbsa.log").split()
            post_exec = """
            cat _MMPBSA_complex_gb.mdout.{0..39} > _MMPBSA_complex_gb.mdout.all
            cat _MMPBSA_complex_gb_surf.dat.{0..39} > _MMPBSA_complex_gb_surf.dat.all
            cat _MMPBSA_complex_pb.mdout.{0..39} > _MMPBSA_complex_pb.mdout.all
            cat _MMPBSA_ligand_gb.mdout.{0..39} > _MMPBSA_ligand_gb.mdout.all
            cat _MMPBSA_ligand_gb_surf.dat.{0..39} > _MMPBSA_ligand_gb_surf.dat.all
            cat _MMPBSA_ligand_pb.mdout.{0..39} > _MMPBSA_ligand_pb.mdout.all
            cat _MMPBSA_receptor_gb.mdout.{0..39} > _MMPBSA_receptor_gb.mdout.all
            cat _MMPBSA_receptor_gb_surf.dat.{0..39} > _MMPBSA_receptor_gb_surf.dat.all
            cat _MMPBSA_receptor_pb.mdout.{0..39} > _MMPBSA_receptor_pb.mdout.all
            rm _MMPBSA_*.{0..39} reference.frc *.pdb *.inpcrd *.mdin* *.out
            """
            t.post_exec = [ x.strip() for x in post_exec.split("\n") ]

            t.cpu_reqs = {
                    'processes': 1,
                    'process_type': None,
                    'threads_per_process': 4,
                    'thread_type': 'OpenMP'
                    }
            t.gpu_reqs = {
                    'processes': 0,
                    'process_type': None,
                    'threads_per_process': 1,
                    'thread_type': 'CUDA'
                    }

            self.s.add_tasks(t)
        self.p.add_stages(self.s)


    def raw_submission_sim_sh(self, rep_count=24):
        
        
        for i in range(1, rep_count + 1):
            t = entk.Task()
            pre_exec = """
             export OMP_NUM_THREADS=1
             export COMP="com"
             export  INPATH="$MEMBERWORK/chm155/inpath/$COMP"
             source ~/.bash_profile
             source ~/.bashrc
             conda activate openmm
             module load cuda gcc spectrum-mpi
             cd $INPATH
            """
            t.pre_exec = [ x.strip() for x in pre_exec.split("\n") ]
            t.pre_exec += [ 
                    "export OUTPATH=\"$INPATH/rep{}\"".format(i),
                    "mkdir -p $OUTPATH",
                    "cd $OUTPATH",
                    "rm -f traj.dcd sim.log"
                    ]

            t.executable = 'python'
            t.arguments = [ '$INPATH/sim.py' ]
            t.post_exec = []

            t.cpu_reqs = {
                    'processes': 1,
                    'process_type': None,
                    'threads_per_process': 4,
                    'thread_type': 'OpenMP'
                    }
            t.gpu_reqs = {
                    'processes': 0,
                    'process_type': None,
                    'threads_per_process': 1,
                    'thread_type': 'CUDA'
                    }
            self.s.add_tasks(t)


    def esmacs_analysis_py(self, energy_files, replicas=None, traj_type="one"):
        t = entk.Task()
        t.executable = 'python'
        t.arguments = [ 'esmacs_analysis.py', '-i={}'.format(energy_files) ]
        if replicas:
            t.arguments += [ '-r={}'.format(replicas) ]
        t.arguments += [ '-t={}'.format(traj_type) ]
        
        t.cpu_reqs = {
                    'processes': 1,
                    'process_type': None,
                    'threads_per_process': 4,
                    'thread_type': 'OpenMP'
                    }
        self.s.add_tasks(t)


    def run(self):
        self.am.workflow = [self.p]
        self.am.run()


if __name__ == "__main__":

    ### raw_submission_esmacs.sh
    esmacs = ESMACS()

    if esmacs.args.task == "esmacs":

        n_nodes = 24
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 10, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : "CHM155_001"
            })
        esmacs.raw_submission_esmacs_sh(rep_count=24)
        esmacs.run()


    elif esmacs.args.task == "sim":

        n_nodes = 4
        esmacs.set_resource(res_dict = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 120, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : "CHM155_001"
            })
        esmacs.raw_submission_sim_sh(rep_count=24)
        esmacs.run()

    
    elif esmacs.args.task == "esmacs_analysis":

        n_nodes = 1
        esmacs.set_resource(res_dict = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 10, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : "CHM155_001"
            })
        esmacs.esmacs_analysis_py()
        esmacs.run()

