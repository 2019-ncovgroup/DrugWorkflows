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
        self.rmq_port = int(os.environ.get('RMQ_PORT', 33239))
        self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', 'two.radical-project.org')

    def set_resource(self, res_desc):
        res_desc["schema"] = "local"
        self.am.resource_desc = res_desc

    def set_argparse(self):
        parser = argparse.ArgumentParser(description="ESMACS")
        parser.add_argument("--task", "-t", help="sim_esmacs, esmacs, or esmacs_analysis")
        args = parser.parse_args()
        self.args = args
        if args.task is None:
            parser.print_help()
            sys.exit(-1)

    def sim_esmacs_py(self, rep_count=24):

        for i in range(1, rep_count + 1):
            t = entk.Task()
            pre_exec = """export OMP_NUM_THREADS=1
                export INPATH="$MEMBERWORK/med110/inpath"
                . /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
                conda activate wf3
                module load cuda/10.1.243 gcc/7.4.0 spectrum-mpi/10.3.1.2-20200121
                mkdir -p $INPATH; cd $INPATH"""
            t.pre_exec = [x.strip() for x in pre_exec.split("\n")]
            t.pre_exec += [
                "export OUTPATH=$INPATH",#"export OUTPATH=\"$INPATH/rep{}\"".format(i),
                "mkdir -p $OUTPATH; cd $OUTPATH",
                "rm -f traj.dcd sim.log"
            ]

            t.executable = '/ccs/home/litan/miniconda3/envs/wf3/bin/python3.7'
            t.arguments = ['$INPATH/sim_esmacs.py', '-i$INPATH', '-n3', '-r{}'.format(i)]
            t.post_exec = []

            t.cpu_reqs = {
                'processes': 1,
                'process_type': None,
                'threads_per_process': 4,
                'thread_type': 'OpenMP'
            }
            t.gpu_reqs = {
                'processes': 1,
                'process_type': None,
                'threads_per_process': 1,
                'thread_type': 'CUDA'
            }

            self.s.add_tasks(t)

        self.p.add_stages(self.s)

    def esmacs_py(self, rep_count=24):#mmpbsa(self):

        for i in range(1, rep_count + 1):
            t = entk.Task()
            t.pre_exec = [ 
                    "export OMP_NUM_THREADS=1",
                    ". /ccs/home/litan/miniconda2/etc/profile.d/conda.sh",
                    "conda activate wf3",
                    "module load cuda/10.1.243 gcc/7.4.0 spectrum-mpi/10.3.1.2-20200121",
                    "export CUDA_HOME=/sw/summit/cuda/10.1.243",
                    "export INPATH=\"$MEMBERWORK/med110/inpath\"", # TODO: parameterized
                    "source /ccs/home/litan/DrugWorkflows/workflow-3/amber18/amber.sh", #TODO: parameterized
                    "export LD_LIBRARY_PATH=\"/sw/summit/cuda/10.1.243/lib:${LD_LIBRARY_PATH}\"",
                    "cd $INPATH",
                    "export OUTPATH=$INPATH/com/rep{}".format(i),
                    "cd $OUTPATH"
                    ]
            t.executable = "MMPBSA.py.MPI"
            t.arguments = ("-O -i $INPATH/esmacs.in -sp " + \
                    "$INPATH/com_sol.prmtop -cp $INPATH/com.prmtop -rp " + \
                    "$INPATH/apo.prmtop -lp $INPATH/lig.prmtop -y traj.dcd " + \
                    "> mmpbsa.log").split()
            post_exec = """cat _MMPBSA_complex_gb.mdout.{0..39} > _MMPBSA_complex_gb.mdout.all
                cat _MMPBSA_complex_gb_surf.dat.{0..39} > _MMPBSA_complex_gb_surf.dat.all
                cat _MMPBSA_complex_pb.mdout.{0..39} > _MMPBSA_complex_pb.mdout.all
                cat _MMPBSA_ligand_gb.mdout.{0..39} > _MMPBSA_ligand_gb.mdout.all
                cat _MMPBSA_ligand_gb_surf.dat.{0..39} > _MMPBSA_ligand_gb_surf.dat.all
                cat _MMPBSA_ligand_pb.mdout.{0..39} > _MMPBSA_ligand_pb.mdout.all
                cat _MMPBSA_receptor_gb.mdout.{0..39} > _MMPBSA_receptor_gb.mdout.all
                cat _MMPBSA_receptor_gb_surf.dat.{0..39} > _MMPBSA_receptor_gb_surf.dat.all
                cat _MMPBSA_receptor_pb.mdout.{0..39} > _MMPBSA_receptor_pb.mdout.all
                rm _MMPBSA_*.{0..39} reference.frc *.pdb *.inpcrd *.mdin* *.out"""
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

        self.p.add_stages(self.s)

    def run(self):
        self.am.workflow = [self.p]
        self.am.run()


if __name__ == "__main__":

    esmacs = ESMACS()

    if esmacs.args.task == "sim_esmacs":

        n_nodes = 4
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 120, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'MED110'
            })
        esmacs.sim_esmacs_py(rep_count=24)
        esmacs.run()

    elif esmacs.args.task == "esmacs":

        n_nodes = 24
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 10, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'MED110'
            })
        esmacs.esmacs_py(rep_count=24)
        esmacs.run()

    elif esmacs.args.task == "esmacs_analysis":

        n_nodes = 1
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 10, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : "MED110"
            })
        esmacs.esmacs_analysis_py()
        esmacs.run()
