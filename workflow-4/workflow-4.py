from radical import entk
import os
import argparse, sys, math

class TIES(object):

    def __init__(self):
        self.set_argparse()
        self._set_rmq()
        #self.am = entk.AppManager(hostname=self.rmq_hostname, port=self.rmq_port)
        self.am = entk.AppManager(hostname=self.rmq_hostname, port=self.rmq_port, username=self.rmq_username, password=self.rmq_password)
        self.p = entk.Pipeline()
        self.s = entk.Stage()
        #self.s1 = entk.Stage()
        #self.s2 = entk.Stage()
        #self.s3 = entk.Stage()

    def _set_rmq(self):
        self.rmq_port = int(os.environ.get('RMQ_PORT', 5672))
        self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', '129.114.17.185')
        self.rmq_username = os.environ.get('RMQ_USERNAME', 'litan')
        self.rmq_password = os.environ.get('RMQ_PASSWORD', 'sccDg7PxE3UjhA5L')

    def set_resource(self, res_desc):
        res_desc["schema"] = "local"
        self.am.resource_desc = res_desc

    def set_argparse(self):
        parser = argparse.ArgumentParser(description="TIES in EnTK")
        parser.add_argument("--task", "-t", help="com or lig")
        #parser.add_argument("--structures", "-i", help="Path to input files")
        #parser.add_argument("--trajectory", "-o", help="Path to output files (default: same as input path)")
        #parser.add_argument("--nanoseconds", "-n", default=6, help="Simulation length (default: 6)")
        #parser.add_argument("--replicas", "-r", default=24, help="Ensemble size for NAMD (default: 24)")
        #parser.add_argument("--component", "-c", default="com", \
        #        help="Component (default: com, complex=com, protein=apo and" \
        #        " ligand=lig)")
        args = parser.parse_args()
        self.args = args
        if args.task is None:
            parser.print_help()
            sys.exit(-1)

    def sim(self, task):

        #os.system("module load namd")
        #os.system(". /home1/07374/litan/miniconda3/etc/profile.d/conda.sh")
        #os.system("conda activate entk")

        if task == 'com':

            '''for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 6):
                    os.system("rm -rf /gpfs/alpine/scratch/litan/med110/ties/com/LAMBDA_{}/rep{}/equilibration/*".format(l, i))
                    os.system("rm -rf /gpfs/alpine/scratch/litan/med110/ties/com/LAMBDA_{}/rep{}/simulation/*".format(l, i))
                    os.system("mkdir -p /gpfs/alpine/scratch/litan/med110/ties/com/LAMBDA_{}/rep{}/equilibration".format(l, i))
                    os.system("mkdir -p /gpfs/alpine/scratch/litan/med110/ties/com/LAMBDA_{}/rep{}/simulation".format(l, i))'''

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 6):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"
                        ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '42', '--tclmain', 'eq0.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 164,#42#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 6):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"
                        ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '42', '--tclmain', 'eq1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 164,#42#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 6):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/com/replica-confs"
                        ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '42', '--tclmain', 'sim1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '5', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 164,#42#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

        elif task == 'lig':

            '''for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 7):
                    os.system("rm -rf /gpfs/alpine/scratch/litan/med110/ties/lig/LAMBDA_{}/rep{}/equilibration/*".format(l, i))
                    os.system("rm -rf /gpfs/alpine/scratch/litan/med110/ties/lig/LAMBDA_{}/rep{}/simulation/*".format(l, i))
                    os.system("mkdir -p /gpfs/alpine/scratch/litan/med110/ties/lig/LAMBDA_{}/rep{}/equilibration".format(l, i))
                    os.system("mkdir -p /gpfs/alpine/scratch/litan/med110/ties/lig/LAMBDA_{}/rep{}/simulation".format(l, i))'''

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 7):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"
                    ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '7', '--tclmain', 'eq0.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 28,#42#164#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 7):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"
                    ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '7', '--tclmain', 'eq1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 28,#42#164#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

            for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
                for i in range(1, 7):
                    t = entk.Task()
                    t.pre_exec = [
                        #"export OMP_NUM_THREADS=1",
                        "module load gcc/8.1.1 spectrum-mpi/10.3.1.2-20200121",
                        "module load fftw/3.3.8",
                        "cd /gpfs/alpine/scratch/litan/med110/ties/lig/replica-confs"
                    ]
                    t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                    t.arguments = ['+ppn', '7', '--tclmain', 'sim1.conf', '{}'.format(l), '{}'.format(i)]#'+replicas', '6', '+pemap', ' 0-83:4,88-171:4', '+commap', ' 0,28,56,88,116,144'
                    t.post_exec = []
                    t.cpu_reqs = {
                        'processes': 1,
                        'process_type': 'MPI',#None
                        'threads_per_process': 28,#42#164#4#4*42
                        'thread_type': 'OpenMP'
                    }
                    self.s.add_tasks(t)

        self.p.add_stages(self.s)
        #self.p.add_stages(self.s1)
        #self.p.add_stages(self.s2)
        #self.p.add_stages(self.s3)

    def run(self):
        self.am.workflow = [self.p]
        self.am.run()


if __name__ == "__main__":

    ties = TIES()

    n_nodes = 65#13#65#5#int(namd.args.replicas)
    ties.set_resource(res_desc = {
        'resource': 'ornl.summit',
        'queue'   : 'debug',
        'walltime': 120, #MIN
        'cpus'    : 168 * n_nodes,
        'gpus'    : 6 * n_nodes,
        'project' : 'MED110'
        })
    ties.sim(task=ties.args.task)
    ties.run()
