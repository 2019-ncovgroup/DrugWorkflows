from radical import entk
import os
import argparse, sys, math

class ESMACS_TIES(object):

    def __init__(self):
        self.set_argparse()
        self._set_rmq()
        #self.am = entk.AppManager(hostname=self.rmq_hostname, port=self.rmq_port)
        self.am = entk.AppManager(hostname=self.rmq_hostname, port=self.rmq_port, username=self.rmq_username, password=self.rmq_password)
        self.p = entk.Pipeline()
        self.s = entk.Stage()

    def _set_rmq(self):
        #self.rmq_port = int(os.environ.get('RMQ_PORT', 33239))
        #self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', 'two.radical-project.org')
        self.rmq_port = int(os.environ.get('RMQ_PORT', 5672))
        self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', '129.114.17.185')
        self.rmq_username = os.environ.get('RMQ_USERNAME', 'litan')
        self.rmq_password = os.environ.get('RMQ_PASSWORD', 'sccDg7PxE3UjhA5L')

    def set_resource(self, res_desc):
        res_desc["schema"] = "local"
        self.am.resource_desc = res_desc

    def set_argparse(self):
        parser = argparse.ArgumentParser(description="ESMACS and TIES")
        parser.add_argument("--task", "-t", help="sim_com, sim_lig, or esmacs")
        parser.add_argument("--structures", "-i", help="Path to input files")
        parser.add_argument("--trajectory", "-o", help="Path to output files (default: same as input path)")
        parser.add_argument("--nanoseconds", "-n", default=3, help="Simulation length (default: 3)")#6
        parser.add_argument("--replicas1", "-r1", default=390, help="Ensemble size for ESMACS with TIES (com) (default: 390)")
        parser.add_argument("--replicas2", "-r2", default=78, help="Ensemble size for ESMACS with TIES (lig) (default: 78)")
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

    def sim_esmacs_com_ties(self, rep_count=390, structures=None, trajectory=None,
                      component="com", nanoseconds=3):#nanoseconds=6

        for i in range(1, int(rep_count) + 1):
            t = entk.Task()
            pre_exec = """export OMP_NUM_THREADS=1
                export WDIR="$MEMBERWORK/med110/inpath"
                . /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
                conda activate wf3
                module load cuda/10.1.243 gcc/7.4.0 spectrum-mpi/10.3.1.2-20200121"""
            t.pre_exec = [x.strip() for x in pre_exec.split("\n")]
            t.executable = '/ccs/home/litan/miniconda3/envs/wf3/bin/python3.7'
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

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 6):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                    ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '42', '--tclmain', 'eq0.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 140,#amounts to 35 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 6):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                    ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '42', '--tclmain', 'eq1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 140,#amounts to 35 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 6):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                    ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '42', '--tclmain', 'sim1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 140,#amounts to 35 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        self.p.add_stages(self.s)

    def sim_esmacs_lig_ties(self, rep_count=78, structures=None, trajectory=None,
                      component="com", nanoseconds=3):#nanoseconds=6

        for i in range(1, int(rep_count) + 1):
            t = entk.Task()
            pre_exec = """export OMP_NUM_THREADS=1
                export WDIR="$MEMBERWORK/med110/inpath"
                . /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
                conda activate wf3
                module load cuda/10.1.243 gcc/7.4.0 spectrum-mpi/10.3.1.2-20200121"""
            t.pre_exec = [x.strip() for x in pre_exec.split("\n")]
            t.executable = '/ccs/home/litan/miniconda3/envs/wf3/bin/python3.7'
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

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 7):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '7', '--tclmain', 'eq0.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 28,#amounts to 7 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 7):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '7', '--tclmain', 'eq1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 28,#amounts to 7 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 7):
                t = entk.Task()
                t.pre_exec = [
                    "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                    "module load fftw/3.3.8",
                    "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"#,
                    #"export OMP_NUM_THREADS=1"
                ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '7', '--tclmain', 'sim1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': 'MPI',#None
                    'threads_per_process': 28,#amounts to 7 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                self.s.add_tasks(t)

        self.p.add_stages(self.s)

    def esmacs_py(self, rep_count=24, component="com", structures=None,
            trajectory=None, nanoseconds=6):

        for i in range(1, int(rep_count) + 1):
            t = entk.Task()
            t.pre_exec = [ 
                    "export OMP_NUM_THREADS=1",
                    ". /ccs/home/litan/miniconda2/etc/profile.d/conda.sh",
                    "conda activate wf3",
                    "module load cuda/10.1.243 gcc/7.4.0 spectrum-mpi/10.3.1.2-20200121",
                    "export CUDA_HOME=/sw/summit/cuda/10.1.243",
                    "export WDIR=\"$MEMBERWORK/med110/inpath\"", 
                    "source /ccs/home/litan/DrugWorkflows/workflow-3/amber18/amber.sh", 
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

    esmacs_ties = ESMACS_TIES()

    if esmacs_ties.args.task == "sim_com":

        n_nodes = math.ceil(float(int(esmacs_ties.args.replicas1)/6))#hardcode 65 nodes for com
        esmacs_ties.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'debug',
            'walltime': 120, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'MED110'
            })
        esmacs_ties.sim_esmacs_com_ties(rep_count=esmacs_ties.args.replicas1,
                component=esmacs_ties.args.component,
                structures=esmacs_ties.args.structures,
                nanoseconds=esmacs_ties.args.nanoseconds,
                trajectory=esmacs_ties.args.trajectory)
        esmacs_ties.run()

    elif esmacs_ties.args.task == "sim_lig":

        n_nodes = math.ceil(float(int(esmacs_ties.args.replicas2)/6))#hardcode 13 nodes for lig
        esmacs_ties.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'debug',
            'walltime': 120, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'MED110'
            })
        esmacs_ties.sim_esmacs_lig_ties(rep_count=esmacs_ties.args.replicas2,
                component=esmacs_ties.args.component,
                structures=esmacs_ties.args.structures,
                nanoseconds=esmacs_ties.args.nanoseconds,
                trajectory=esmacs_ties.args.trajectory)
        esmacs_ties.run()

    elif esmacs_ties.args.task == "esmacs":

        n_nodes = int(esmacs_ties.args.replicas)
        esmacs_ties.set_resource(res_desc = {
            'resource': 'ornl.summit',
            'queue'   : 'batch',
            'walltime': 5, #MIN
            'cpus'    : 168 * n_nodes,
            'gpus'    : 6 * n_nodes,
            'project' : 'MED110'
            })
        esmacs_ties.esmacs_py(rep_count=esmacs_ties.args.replicas, 
                component=esmacs_ties.args.component,
                structures=esmacs_ties.args.structures,
                nanoseconds=esmacs_ties.args.nanoseconds,
                trajectory=esmacs_ties.args.trajectory)
        esmacs_ties.run()
