import os
import sys
import json
import time
import uuid
import itertools
from pathlib import Path

import radical.utils as ru

from radical.entk import Pipeline, Stage, Task, AppManager

# Assumptions:
# - # of MD steps: 2
# - Each MD step runtime: 15 minutes
# - Summit's scheduling policy [1]
#
# Resource rquest:
# - 4 <= nodes with 2h walltime.
#
# Workflow [2]
#
# [1] https://www.olcf.ornl.gov/for-users/system-user-guides/summit/summit-user-guide/scheduling-policy
# [2] https://docs.google.com/document/d/1XFgg4rlh7Y2nckH0fkiZTxfauadZn_zSn3sh51kNyKE/
#
'''
export RADICAL_PILOT_PROFILE=True
export RADICAL_ENTK_PROFILE=True
'''

def get_ligand_topology(pdb_file, topol_dir):
    # Assume abspath is passed and that ligand ID is enoded in pdb_file name
    # pdb_file: /path/system_<ligid>.pdb
    # topol:    /path/topology_<ligid>.pdb
    #topol_dir = '/gpfs/alpine/med110/scratch/atrifan2/PLPro_ligands/gb_plpro/DrugWorkflows/workflow-2/top_dir/'
    pdb_filename = os.path.basename(pdb_file)
    ligid = pdb_filename.split('_')[1]
    if '.pdb' in ligid:
        ligid = ligid[:-4]
    return os.path.join(topol_dir, f'topology_{ligid}.prmtop')


def generate_training_pipeline(cfg):
    """
    Function to generate the CVAE_MD pipeline
    """
    CUR_STAGE = cfg['CUR_STAGE']
    MAX_STAGE = cfg['MAX_STAGE']

    def generate_MD_stage(num_MD=1):
        """
        Function to generate MD stage.
        """
        s1 = Stage()
        s1.name = 'MD'
        
        outlier_filepath = '%s/Outlier_search/restart_points.json' % cfg['base_path']
        initial_MD = True
        if os.path.exists(outlier_filepath):
            initial_MD = False
            with open(outlier_filepath, "r") as f:
                outlier_list = json.load(f)
        else:
            outlier_list = Path(cfg["pdb_dir"]).glob("*.pdb")
            outlier_list = [p.as_posix() for p in outlier_list]

        print('Number of outliers in stage 1:', len(outlier_list))

        # Keep looping around outlier_list in case num_MD > len(outlier_list)
        outlier_list = itertools.cycle(outlier_list)

        # MD tasks
        global time_stamp
        time_stamp = int(time.time())

        print('time_stamp:', time_stamp)

        for i in range(num_MD):
            t1 = Task()
            
            # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/MD_exps/fs-pep/run_openmm.py
            t1.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh']
            t1.pre_exec += ['module load cuda/9.1.85']
            t1.pre_exec += ['conda activate %s' % cfg['conda_openmm']]
            t1.pre_exec += ['export PYTHONPATH=%s/MD_exps:%s/MD_exps/MD_utils:$PYTHONPATH' %
                (cfg['base_path'], cfg['base_path'])]
            t1.pre_exec += ['cd %s/MD_exps/%s' % (cfg['base_path'], cfg['system_name'])]
            t1.pre_exec += ['mkdir -p omm_runs_%d && cd omm_runs_%d' % (time_stamp+i, time_stamp+i)]
           
            t1.executable = ['%s/bin/python' % cfg['conda_openmm']]  # run_openmm.py
            t1.arguments = ['%s/MD_exps/%s/run_openmm.py' % (cfg['base_path'], cfg['system_name'])]

            # pick initial point of simulation
            print('Getting PDB')
            pdb_file = next(outlier_list)
            top_file = get_ligand_topology(pdb_file, cfg['top_dir'])
            print('pdb_file:', pdb_file)
            print('top_file:', top_file)

            t1.arguments += ['--pdb_file', pdb_file,
                             '--topol', top_file]
            t1.pre_exec += ['cp %s ./' % pdb_file]

            # how long to run the simulation
            if initial_MD:
                t1.arguments += ['--length', cfg['LEN_initial']]
            else:
                t1.arguments += ['--length', cfg['LEN_iter']]

            # assign hardware the task
            t1.cpu_reqs = {'processes'          : 1,
                           'process_type'       : None,
                           'threads_per_process': 4,
                           'thread_type'        : 'OpenMP'}
            t1.gpu_reqs = {'processes'          : 1,
                           'process_type'       : None,
                           'threads_per_process': 1,
                           'thread_type'        : 'CUDA'}

            # Add the MD task to the simulating stage
            s1.add_tasks(t1)

        return s1

    def generate_preprocessing_stage(num_MD=1):

        global time_stamp
        s_1 = Stage()
        s_1.name = 'preprocessing'
        
        for i in range(num_MD):

            t_1 = Task()

            omm_dir = 'omm_runs_%s' % (time_stamp + i)

            print('omm_dir', omm_dir)

            t_1.pre_exec = [
                '. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh',
                'conda activate %s' % cfg['conda_pytorch'],
                'export LANG=en_US.utf-8',
                'export LC_ALL=en_US.utf-8',
                'cd %s/MD_exps/%s/%s/' % (cfg['base_path'], cfg['system_name'], omm_dir),
                #'echo $(pwd)',
                #'echo $(ls)',
                #'cd %s' % omm_dir,
                'export PDB_FILE=$(ls | grep .pdb)']
        
            t_1.executable = ['%s/bin/python' % (cfg['conda_pytorch'])] 

            output_h5 = f'{cfg["h5_tmp_dir"]}/output_{uuid.uuid4()}.h5'

            t_1.arguments = [
                '%s/scripts/traj_to_dset.py' % cfg['molecules_path'],
                '-t', '.', #'output.dcd',
                '-p', '${PDB_FILE}',
                '-r', '${PDB_FILE}',
                '-o', '%s' % output_h5,
                '--contact_maps_parameters',
                "kernel_type=threshold,threshold=%s" % cfg['cutoff'],
                '-s', cfg['selection'],
                '--rmsd',
                '--fnc',
                '--contact_map',
                '--point_cloud',
                '--verbose']

            # Add the aggregation task to the aggreagating stage
            t_1.cpu_reqs = {
                'processes': 1,
                'process_type': None,
                'threads_per_process': 4,
                'thread_type': 'OpenMP'
            }

            s_1.add_tasks(t_1)
        
        
        return s_1

    def generate_aggregating_stage():
        """
        Function to concatenate the MD trajectory (h5 contact map)
        """
        s2 = Stage()
        s2.name = 'aggregating'

        # Aggregation task
        t2 = Task()
        
        # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/MD_to_CVAE/MD_to_CVAE.py
        t2.pre_exec = [
                '. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh',
                'conda activate %s' % cfg['conda_pytorch'],
                'export LANG=en_US.utf-8',
                'export LC_ALL=en_US.utf-8']
        # preprocessing for molecules' script, it needs files in a single
        # directory
        # the following pre-processing does:
        # 1) find all (.dcd) files from openmm results
        # 2) create a temp directory
        # 3) symlink them in the temp directory
        #

        #t2.pre_exec += [
        #        'export dcd_list=(`ls %s/MD_exps/%s/omm_runs_*/*dcd`)' % (cfg['base_path'], cfg['system_name']),
        #        'export tmp_path=`mktemp -p %s/MD_to_CVAE/ -d`' % cfg['base_path'],
        #        'for dcd in ${dcd_list[@]}; do tmp=$(basename $(dirname $dcd)); ln -s $dcd $tmp_path/$tmp.dcd; done',
        #        'ln -s %s $tmp_path/prot.pdb' % cfg['pdb_file'],
        #        'ls ${tmp_path}']
            
        #t2.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']

        #node_cnt_constraint = cfg['md_counts'] * max(1, CUR_STAGE) // 12
        #cmd_cat    = 'cat /dev/null'
        #cmd_jsrun  = 'jsrun -n %s -r 1 -a 6 -c 7 -d packed' % min(cfg['node_counts'], node_cnt_constraint)
 
        t2.executable = ['%s/bin/python' % cfg['conda_pytorch']]  # MD_to_CVAE.py
         
        t2.arguments = [
                '%s/scripts/concat_dsets.py' % cfg['molecules_path'],
                '-d', cfg['h5_tmp_dir'],
                '-o', '%s/MD_to_CVAE/cvae_input.h5' % cfg['base_path'],
                '--rmsd',
                '--fnc',
                '--contact_map',
                '--point_cloud',
                '--verbose']

        # Add the aggregation task to the aggreagating stage
        t2.cpu_reqs = {'processes'          : 1,
                       'process_type'       : None,
                       'threads_per_process': 4,
                       'thread_type'        : 'OpenMP'}

        s2.add_tasks(t2)
        return s2


    def generate_ML_stage(num_ML=1):
        """
        Function to generate the learning stage
        """
        # learn task
        time_stamp = int(time.time())
        s3 = Stage()
        s3.name = 'learning'
        for i in range(num_ML):

            t3 = Task()
            # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/CVAE_exps/train_cvae.py
            t3.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh']
            t3.pre_exec += ['module load gcc/7.4.0',
                            'module load cuda/10.1.243',
                            'export LANG=en_US.utf-8',
                            'export LC_ALL=en_US.utf-8',
                            'export HDF5_USE_FILE_LOCKING=FALSE']
            t3.pre_exec += ['conda activate %s' % cfg['conda_pytorch']]
            dim = i + 3
            cvae_dir = 'cvae_runs_%.2d_%d' % (dim, time_stamp+i)
            t3.pre_exec += ['cd %s/CVAE_exps' % cfg['base_path']]
            
            t3.pre_exec += ['export LD_LIBRARY_PATH=/gpfs/alpine/proj-shared/med110/atrifan/scripts/cuda/targets/ppc64le-linux/lib/:$LD_LIBRARY_PATH']
            #t3.pre_exec += ['mkdir -p %s && cd %s' % (cvae_dir, cvae_dir)] # model_id creates sub-dir
            # this is for ddp, distributed
            t3.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']
            #pnodes = cfg['node_counts'] // num_ML # partition
            pnodes = 1#max(1, pnodes)

            hp = cfg['ml_hpo'][i]
            cmd_cat    = 'cat /dev/null'
            #cmd_jsrun  = 'jsrun -n %s -r 1 -g %s -a %s -c %s -d packed'% (pnodes)

            cmd_jsrun  = 'jsrun -n %s -g %s -a %s -c %s -d packed' % (pnodes, cfg['gpu_per_node'], cfg['gpu_per_node'], cfg['cpu_per_node'])

            # VAE config
            # cmd_vae    = '%s/examples/run_vae_dist_summit_entk.sh' % cfg['molecules_path']
            # cmd_sparse = ' '.join(['%s/MD_to_CVAE/cvae_input.h5' % cfg["base_path"],
            #                        "./", cvae_dir, 'sparse-concat', 'resnet',
            #                        str(cfg['residues']), str(cfg['residues']),
            #                        str(hp['latent_dim']), 'amp', 'non-distributed',
            #                        str(hp['batch_size']), str(cfg['epoch']),
            #                        str(cfg['sample_interval']),
            #                        hp['optimizer'], cfg['init_weights']])

            # AAE config
            
            if CUR_STAGE > 0:
                # Get latest model weights
                model_paths = Path(cfg["base_path"]).joinpath("CVAE_exps").glob("model-cvae_runs*")
                model_paths = sorted(model_paths, key=lambda p: int(p.name.split("_")[-1])) # Sort by timestamp
                latest_model_path = list(model_paths)[-1] # Get latest model run
                weights_path = latest_model_path.joinpath("checkpoint").glob("*.pt") # Glob checkpoints
                # Checkpoints have format epoch-1-20201207-143335.pt
                weights_path = sorted(weights_path, key=lambda p: int(p.name.split("-")[1]))
                latest_weights_path = "-iw " + list(weights_path)[-1].as_posix()
            elif "init_weights" in cfg:
                # Use pretrained model
                latest_weights_path = "-iw " + cfg["init_weights"]
            else:
                # Train from scratch
                latest_weights_path = ""

            print(f"CUR_STAGE: {CUR_STAGE} using weights {latest_weights_path}")

            cmd_vae    = '%s/examples/bin/run_aae_dist_entk.sh' % cfg['molecules_path']
            t3.executable = ["%s/bin/python" % cfg["conda_pytorch"]]
            t3.arguments = [
                "%s/examples/example_aae.py" % cfg["molecules_path"],
                "-i",  "%s/MD_to_CVAE/cvae_input.h5" % cfg["base_path"],
                "-o", "./",
                #"--distributed",
                "-m", cvae_dir,
                "-dn", "point_cloud",
                "-rn", "rmsd",
                "--encoder_kernel_sizes", 5, 3, 3, 1, 1,
                "-nf", 0,
                "-np", str(cfg["residues"]),
                "-e", str(cfg["epoch"]),
                "-b", str(hp["batch_size"]),
                "-opt", hp["optimizer"],
                latest_weights_path,
                "-lw", hp["loss_weights"],
                "-S", str(cfg["sample_interval"]),
                "-ti", str(int(cfg["epoch"]) + 1),
                "-d", str(hp["latent_dim"]),
                "--num_data_workers", 0,
                '-E', '0',
                '-D', '0',
                '-G', '0']

            #+ f'{cfg['molecules_path']}/examples/run_vae_dist_summit.sh -i {sparse_matrix_path} -o ./ --model_id {cvae_dir} -f sparse-concat -t resnet --dim1 168 --dim2 168 -d 21 --amp --distributed -b {batch_size} -e {epoch} -S 3']
        #     ,
        #             '-i', sparse_matrix_path,
        #             '-o', './',
        #             '--model_id', cvae_dir,
        #             '-f', 'sparse-concat',
        #             '-t', 'resnet',
        #             # fs-pep
        #             '--dim1', 168,
        #             '--dim2', 168,
        #             '-d', 21,
        #             '--amp',      # sparse matrix
        #             '--distributed',
        #             '-b', batch_size, # batch size
        #             '-e', epoch,# epoch
        #             '-S', 3
        #             ]

            t3.cpu_reqs = {'processes'          : 1,
                           'process_type'       : None,
                           'threads_per_process': 4,
                           'thread_type'        : 'OpenMP'}
            t3.gpu_reqs = {'processes'          : 1,
                           'process_type'       : None,
                           'threads_per_process': 1,
                           'thread_type'        : 'CUDA'}

            # Add the learn task to the learning stage
            s3.add_tasks(t3)
        return s3


    def generate_interfacing_stage():
        s4 = Stage()
        s4.name = 'scanning'

        # Scaning for outliers and prepare the next stage of MDs
        t4 = Task()

        t4.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh']
        t4.pre_exec += ['conda activate %s' % cfg['conda_pytorch']]
        t4.pre_exec += ['mkdir -p %s/Outlier_search/outlier_pdbs' % cfg['base_path']]
        t4.pre_exec += ['export models=""; for i in `ls -d %s/CVAE_exps/model-cvae_runs*/`; do if [ "$models" != "" ]; then    models=$models","$i; else models=$i; fi; done;cat /dev/null' % cfg['base_path']]
        t4.pre_exec += ['export LANG=en_US.utf-8', 'export LC_ALL=en_US.utf-8']
        t4.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']

        cmd_cat = 'cat /dev/null'
        #cmd_jsrun = 'jsrun -n %s -a 6 -g 6 -r 1 -c 7' % cfg['node_counts']

        cmd_jsrun = 'jsrun -n %s -a %s -g %s -r 1 -c %s' % (cfg['node_counts'], cfg['gpu_per_node'], cfg['gpu_per_node'], cfg['cpu_per_node'] // cfg['gpu_per_node'])

        #molecules_path = '/gpfs/alpine/world-shared/ven201/tkurth/molecules/'
        t4.executable = [' %s; %s %s/examples/outlier_detection/run_optics_dist_entk.sh' % (cmd_cat, cmd_jsrun, cfg['molecules_path'])]
        t4.arguments = ['%s/bin/python' % cfg['conda_pytorch']]
        t4.arguments += ['%s/examples/outlier_detection/optics.py' % cfg['molecules_path'],
                        '--sim_path', '%s/MD_exps/%s' % (cfg['base_path'], cfg['system_name']),
                        '--pdb_out_path', '%s/Outlier_search/outlier_pdbs' % cfg['base_path'],
                        '--restart_points_path',
                        '%s/Outlier_search/restart_points.json' % cfg['base_path'],
                        '--data_path', '%s/MD_to_CVAE/cvae_input.h5' % cfg['base_path'],
                        '--model_paths', '$models',
                        '--model_type', cfg['model_type'],
                        '--min_samples', 10,
                        '--n_outliers', cfg['md_counts'] + 1,
                        '--dim1', cfg['residues'],
                        '--dim2', cfg['residues'],
                        '--cm_format', 'sparse-concat',
                        '--batch_size', cfg['batch_size'],
                        '--distributed']

        t4.cpu_reqs = {'processes'          : 6 * cfg['node_counts'] or 1,
                       'process_type'       : 'MPI',
                       'threads_per_process': cfg['gpu_per_node'] * 4,
                       'thread_type'        : 'OpenMP'}
        t4.gpu_reqs = {'processes'          : 1,
                       'process_type'       : 'MPI',
                       'threads_per_process': 1,
                       'thread_type'        : 'CUDA'}
        
        s4.add_tasks(t4)
        s4.post_exec = func_condition
        return s4


    def func_condition():
        nonlocal CUR_STAGE
        nonlocal MAX_STAGE
        if CUR_STAGE < MAX_STAGE:
            func_on_true()
        else:
            func_on_false()

    def func_on_true():
        nonlocal CUR_STAGE
        nonlocal MAX_STAGE
        print('finishing stage %d of %d' % (CUR_STAGE, MAX_STAGE))

        # --------------------------
        # MD stage
        #
        s1 = generate_MD_stage(num_MD=cfg['md_counts'])
        # Add simulating stage to the training pipeline
        p.add_stages(s1)

        # Data Preprocessing stage
        s_1 = generate_preprocessing_stage(num_MD=cfg['md_counts'])
        p.add_stages(s_1)

        # --------------------------
        # Aggregate stage
        s2 = generate_aggregating_stage()
        p.add_stages(s2)

        if CUR_STAGE % cfg['RETRAIN_FREQ'] == 0:
            # --------------------------
            # Learning stage
            s3 = generate_ML_stage(num_ML=cfg['ml_counts'])
            # Add the learning stage to the pipeline
            p.add_stages(s3)

        # --------------------------
        # Outlier identification stage
        s4 = generate_interfacing_stage()
        p.add_stages(s4)

        CUR_STAGE += 1

    def func_on_false():
        print ('Done')

    p = Pipeline()
    p.name = 'MD_ML'

    # --------------------------
    # MD stage
    s1 = generate_MD_stage(num_MD=cfg['md_counts'])
    # Add simulating stage to the training pipeline
    p.add_stages(s1)

    # Data Preprocessing stage
    s_1 = generate_preprocessing_stage(num_MD=cfg['md_counts'])
    p.add_stages(s_1)

    # --------------------------
    # Aggregate stage
    s2 = generate_aggregating_stage()
    # Add the aggregating stage to the training pipeline
    p.add_stages(s2)

    # --------------------------
    # Learning stage
    s3 = generate_ML_stage(num_ML=cfg['ml_counts'])
    # Add the learning stage to the pipeline
    p.add_stages(s3)
    
    # --------------------------
    # Outlier identification stage
    s4 = generate_interfacing_stage()
    p.add_stages(s4)

    CUR_STAGE += 1
    
    # REMOVE if you run pipeline again
    #func_on_true()

    return p


# ------------------------------------------------------------------------------
if __name__ == '__main__':

    reporter = ru.Reporter(name='radical.entk')
    reporter.title('COVID-19 - Workflow2')

    # resource specified as argument
    if len(sys.argv) == 2:
        cfg_file = sys.argv[1]
    elif sys.argv[0] == "molecules_adrp.py":
        cfg_file = "adrp_system.json"
    elif sys.argv[0] == "molecules_3clpro.py":
        cfg_file = "3clpro_system.json"
    else:
        reporter.exit('Usage:\t%s [config.json]\n\n' % sys.argv[0])

    cfg = ru.Config(cfg=ru.read_json(cfg_file))
    cfg['node_counts'] = max(1, cfg['md_counts'] // cfg['gpu_per_node'])

    res_dict = {
            'resource': cfg['resource'],
            'queue'   : cfg['queue'],
            'schema'  : cfg['schema'],
            'walltime': cfg['walltime'],
            'project' : cfg['project'],
            'cpus'    : 42 * 4 * cfg['node_counts'],
            'gpus'    : cfg['gpu_per_node'] * cfg['node_counts']
    }

    # Create Application Manager
    appman = AppManager(hostname=os.environ.get('RMQ_HOSTNAME'),
                        port=int(os.environ.get('RMQ_PORT')),
                        username=os.environ.get('RMQ_USERNAME'),
                        password=os.environ.get('RMQ_PASSWORD'))
    appman.resource_desc = res_dict

    p1 = generate_training_pipeline(cfg)
    pipelines = [p1]

    # Assign the workflow as a list of Pipelines to the Application Manager. In
    # this way, all the pipelines in the list will execute concurrently.
    appman.workflow = pipelines

    # Run the Application Manager
    appman.run()
