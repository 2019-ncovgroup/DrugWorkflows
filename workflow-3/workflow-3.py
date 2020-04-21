from radical import entk
import os
import argparse, sys, math

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
        parser.add_argument("--task", "-t", help="sim_esmacs or esmacs")
        parser.add_argument("--structures", "-i", help="Path to input files")
        parser.add_argument("--trajectory", "-o", help="Path to output files (default: same as input path)")
        parser.add_argument("--nanoseconds", "-n", default=6, help="Simulation length (default: 6)")
        parser.add_argument("--replicas", "-r", default=24, help="Ensemble size for ESMACS (default: 24)")
        parser.add_argument("--component", "-c", default="com", \
                help="Component (default: com, complex=com, protein=apo and" \
                " ligand=lig)")
        args = parser.parse_args()
        self.args = args
        if args.task is None or args.structures is None:
            parser.print_help()
            sys.exit(-1)
        elif args.trajectory is None:
            args.trajectory = args.structures

    def sim_esmacs_py(self, rep_count=24, structures=None, trajectory=None,
                      component="com", nanoseconds=6):

        for i in range(1, int(rep_count) + 1):
            t = entk.Task()
            pre_exec = """export OMP_NUM_THREADS=1
                export WDIR="$MEMBERWORK/chm155/Model-generation"
                . /gpfs/alpine/scratch/apbhati/chm155/miniconda/etc/profile.d/conda.sh
                conda activate conda-entk
                module load cuda gcc spectrum-mpi"""
            t.pre_exec = [x.strip() for x in pre_exec.split("\n")]
            t.executable = '/gpfs/alpine/scratch/apbhati/chm155/miniconda/envs/conda-entk/bin/python'
            t.arguments = ['$WDIR/sim_esmacs.py', '-i{}'.format(structures), '-o{}'.format(trajectory), '-n{}'.format(nanoseconds), '-c{}'.format(component), '-r{}'.format(i)]
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

    def esmacs_py(self, rep_count=24, component="com", structures=None,
            trajectory=None, nanoseconds=6):

        for i in range(1, int(rep_count) + 1):
            t = entk.Task()
            t.pre_exec = [ 
                    "export OMP_NUM_THREADS=1",
                    ". /gpfs/alpine/scratch/apbhati/chm155/miniconda/etc/profile.d/conda.sh",
                    "conda activate conda-entk",
                    "module load cuda/10.1.243 gcc/6.4.0 spectrum-mpi/10.3.1.2-20200121",
                    "export CUDA_HOME=/sw/summit/cuda/10.1.243",
                    "export WDIR=\"$MEMBERWORK/chm155/Model-generation\"", 
                    "source /gpfs/alpine/scratch/apbhati/chm155/AmberTools19/amber18/amber.sh", 
                    "export LD_LIBRARY_PATH=\"/sw/summit/cuda/10.1.243/lib:${LD_LIBRARY_PATH}\"",
                    "export INPATH={}".format(structures),
                    "export COM={}".format(component),
                    "cd {}/{}/rep{}".format(trajectory, component, i)
                    ]
            # Amber
            t.executable = "MMPBSA.py.MPI"
            if component == "com":
                t.arguments = ("-O -i $WDIR/impress_md/esmacs.in -sp " + \
                        "$INPATH/${COM}_sol.prmtop -cp $INPATH/com.prmtop -rp " + \
                        "$INPATH/apo.prmtop -lp $INPATH/lig.prmtop -y traj.dcd " + \
                        "> mmpbsa.log").split()
                post_exec = """ls _MMPBSA_complex_gb.mdout.* | sort -V | xargs cat > _MMPBSA_complex_gb.mdout.all
                ls _MMPBSA_complex_gb_surf.dat.* | sort -V | xargs cat > _MMPBSA_complex_gb_surf.dat.all
                ls _MMPBSA_complex_pb.mdout.* | sort -V | xargs cat > _MMPBSA_complex_pb.mdout.all
                ls _MMPBSA_ligand_gb.mdout.* | sort -V | xargs cat > _MMPBSA_ligand_gb.mdout.all
                ls _MMPBSA_ligand_gb_surf.dat.* | sort -V | xargs cat > _MMPBSA_ligand_gb_surf.dat.all
                ls _MMPBSA_ligand_pb.mdout.* | sort -V | xargs cat > _MMPBSA_ligand_pb.mdout.all
                ls _MMPBSA_receptor_gb.mdout.* | sort -V | xargs cat > _MMPBSA_receptor_gb.mdout.all
                ls _MMPBSA_receptor_gb_surf.dat.* | sort -V | xargs cat > _MMPBSA_receptor_gb_surf.dat.all
                ls _MMPBSA_receptor_pb.mdout.* | sort -V | xargs cat > _MMPBSA_receptor_pb.mdout.all
                rm _MMPBSA_*.[0-9]* reference.frc *.inpcrd *.mdin* *.out"""
            else:
                t.arguments = ("-O -i $WDIR/impress_md/esmacs.in -sp " + \
                        "$INPATH/${COM}_sol.prmtop -cp $INPATH/$COM.prmtop " + \
                        "-y traj.dcd > mmpbsa.log").split()
                post_exec = """ls _MMPBSA_complex_gb.mdout.* | sort -V | xargs cat > _MMPBSA_complex_gb.mdout.all
                ls _MMPBSA_complex_gb_surf.dat.* | sort -V | xargs cat > _MMPBSA_complex_gb_surf.dat.all
                ls _MMPBSA_complex_pb.mdout.* | sort -V | xargs cat > _MMPBSA_complex_pb.mdout.all
                rm _MMPBSA_*.[0-9]* reference.frc *.inpcrd *.mdin* *.out"""
            t.post_exec = [ x.strip() for x in post_exec.split("\n") ]
            t.post_exec = ["cd {}/{}/rep{}".format(trajectory, component, i)] + t.post_exec

            t.cpu_reqs = {
                    'processes': (int(nanoseconds)-2)*10,
                    'process_type': 'MPI',
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

    def run(self):
        self.am.workflow = [self.p]
        self.am.run()


if __name__ == "__main__":

    esmacs = ESMACS()

    if esmacs.args.task == "sim_esmacs":

        n_nodes = math.ceil(float(int(esmacs.args.replicas)/6))
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 10, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'CHM155_001'
            })
        esmacs.sim_esmacs_py(rep_count=esmacs.args.replicas,
                component=esmacs.args.component,
                structures=esmacs.args.structures,
                nanoseconds=esmacs.args.nanoseconds,
                trajectory=esmacs.args.trajectory)
        esmacs.run()

    elif esmacs.args.task == "esmacs":

        n_nodes = int(esmacs.args.replicas)
        esmacs.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 5, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'CHM155_001'
            })
        esmacs.esmacs_py(rep_count=esmacs.args.replicas, 
                component=esmacs.args.component,
                structures=esmacs.args.structures,
                nanoseconds=esmacs.args.nanoseconds,
                trajectory=esmacs.args.trajectory)
        esmacs.run()

