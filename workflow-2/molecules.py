import os
import sys
import json
import time

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
        
        initial_MD = True
        outlier_filepath = '%s/Outlier_search/restart_points.json' % cfg['base_path']
        
        if os.path.exists(outlier_filepath):
            initial_MD = False
            outlier_file = open(outlier_filepath, 'r')
            outlier_list = json.load(outlier_file)
            outlier_file.close()

        # MD tasks
        time_stamp = int(time.time())
        for i in range(num_MD):
            t1 = Task()
            
            # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/MD_exps/fs-pep/run_openmm.py
            t1.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh || true']
            t1.pre_exec += ['module load cuda/9.1.85']
            t1.pre_exec += ['conda activate %s' % cfg['conda_openmm']]
            t1.pre_exec += ['export PYTHONPATH=%s/MD_exps:%s/MD_exps/MD_utils:$PYTHONPATH' %
                (cfg['base_path'], cfg['base_path'])]
            t1.pre_exec += ['cd %s/MD_exps/%s' % (cfg['base_path'], cfg['system_name'])]
            t1.pre_exec += ['mkdir -p omm_runs_%d && cd omm_runs_%d' % (time_stamp+i, time_stamp+i)]
            
            t1.executable = ['%s/bin/python' % cfg['conda_openmm']]  # run_openmm.py
            t1.arguments = ['%s/MD_exps/%s/run_openmm.py' % (cfg['base_path'], cfg['system_name'])]
            #t1.arguments += ['--topol', '%s/MD_exps/fs-pep/pdb/topol.top' % cfg['base_path']]
           
            if 'top_file' in cfg:
                t1.arguments += ['--topol', cfg['top_file']]

            # pick initial point of simulation
            if initial_MD or i >= len(outlier_list):
                t1.arguments += ['--pdb_file', cfg['pdb_file'] ]
            elif outlier_list[i].endswith('pdb'):
                t1.arguments += ['--pdb_file', outlier_list[i]]
                t1.pre_exec += ['cp %s ./' % outlier_list[i]]
            elif outlier_list[i].endswith('chk'):
                t1.arguments += ['--pdb_file', cfg['pdb_file'],
                        '-c', outlier_list[i]]
                t1.pre_exec += ['cp %s ./' % outlier_list[i]]

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
                '. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh || true',
                'conda activate %s' % cfg['conda_pytorch'],
                'export LANG=en_US.utf-8',
                'export LC_ALL=en_US.utf-8']
        # preprocessing for molecules' script, it needs files in a single
        # directory
        # the following pre-processing does:
        # 1) find all (.dcd) files from openmm results
        # 2) create a temp directory
        # 3) symlink them in the temp directory
        t2.pre_exec += [
                'export dcd_list=(`ls %s/MD_exps/%s/omm_runs_*/*dcd`)' % (cfg['base_path'], cfg['system_name']),
                'export tmp_path=`mktemp -p %s/MD_to_CVAE/ -d`' % cfg['base_path'],
                'for dcd in ${dcd_list[@]}; do tmp=$(basename $(dirname $dcd)); ln -s $dcd $tmp_path/$tmp.dcd; done',
                'ln -s %s $tmp_path/prot.pdb' % cfg['pdb_file'],
                'ls ${tmp_path}']
            
        t2.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']

        # - Each node takes 6 ranks
        # - each rank processes 2 files
        # - each iteration accumulates files to process
        cnt_constraint = min(cfg['node_counts'] * 6, cfg['md_counts'] * max(1,
            CUR_STAGE) // 2)
 
        t2.executable = ['%s/bin/python' % (cfg['conda_pytorch'])]  # MD_to_CVAE.py
        t2.arguments = [
                '%s/scripts/traj_to_dset.py' % cfg['molecules_path'],
                '-t', '$tmp_path',
                '-p', '%s/Parameters/input_protein/prot.pdb' % cfg['base_path'],
                '-r', '%s/Parameters/input_protein/prot.pdb' % cfg['base_path'],
                '-o', '%s/MD_to_CVAE/cvae_input.h5' % cfg['base_path'],
                '--contact_maps_parameters',
                "kernel_type=threshold,threshold=%s" % cfg['cutoff'],
                '-s', cfg['selection'],
                '--rmsd',
                '--fnc',
                '--contact_map',
                '--point_cloud',
                '--num_workers', 2,
                '--distributed',
                '--verbose']

        # Add the aggregation task to the aggreagating stage
        t2.cpu_reqs = {'processes'          : 1 * cnt_constraint,
                       'process_type'       : "MPI",
                       'threads_per_process': 6 * 4,
                       'thread_type'        : 'OpenMP'}

        s2.add_tasks(t2)
        return s2


    def generate_ML_stage(num_ML=1):
        """
        Function to generate the learning stage
        """
        # learn task
        time_stamp = int(time.time())
        stages = []
        for i in range(num_ML):
            s3 = Stage()
            s3.name = 'learning'

            t3 = Task()
            # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/CVAE_exps/train_cvae.py
            t3.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh || true']
            t3.pre_exec += ['module load gcc/7.3.1',
                            'module load cuda/10.1.243',
                            'export LANG=en_US.utf-8',
                            'export LC_ALL=en_US.utf-8']
            t3.pre_exec += ['conda activate %s' % cfg['conda_pytorch']]
            dim = i + 3
            cvae_dir = 'cvae_runs_%.2d_%d' % (dim, time_stamp+i)
            t3.pre_exec += ['cd %s/CVAE_exps' % cfg['base_path']]
            t3.pre_exec += ['export LD_LIBRARY_PATH=/usr/workspace/cv_ddmd/lee1078/anaconda/envs/cuda/targets/ppc64le-linux/lib/:$LD_LIBRARY_PATH']
            #t3.pre_exec += ['mkdir -p %s && cd %s' % (cvae_dir, cvae_dir)] # model_id creates sub-dir
            # this is for ddp, distributed
            t3.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']
            #pnodes = cfg['node_counts'] // num_ML # partition
            pnodes = 1#max(1, pnodes)

            hp = cfg['ml_hpo'][i]
            cmd_cat    = 'cat /dev/null'
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
            cmd_vae    = '%s/examples/bin/run_aae_dist_entk.sh' % cfg['molecules_path']
         
            t3.executable = ['%s; %s %s' % (cmd_cat, cmd_jsrun, cmd_vae)]
            t3.arguments = ['%s/bin/python' % cfg['conda_pytorch']]
            t3.arguments += ['%s/examples/example_aae.py' % cfg['molecules_path'],
                            '-i', '%s/MD_to_CVAE/cvae_input.h5' % cfg["base_path"], 
                            '-o', './',
                            '--distributed',
                            '-m', cvae_dir,
                            '-dn', 'point_cloud',
                            '-rn', 'rmsd',
                            '--encoder_kernel_sizes', '5', '3', '3', '1', '1',
                            '-nf', '0',
                            '-np', str(cfg['residues']),
                            '-e', str(cfg['epoch']),
                            '-b', str(hp['batch_size']),
                            '-opt', hp['optimizer'], 
                            '-iw', cfg['init_weights'],
                            '-lw', hp['loss_weights'],
                            '-S', str(cfg['sample_interval']),
                            '-ti', str(int(cfg['epoch']) + 1),
                            '-d', str(hp['latent_dim']),
                            '--num_data_workers', '0']

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

            t3.cpu_reqs = {'processes'          : 6,
                           'process_type'       : 'MPI',
                           'threads_per_process': 4,
                           'thread_type'        : 'OpenMP'}
            t3.gpu_reqs = {'processes'          : 1,
                           'process_type'       : 'MPI',
                           'threads_per_process': 1,
                           'thread_type'        : 'CUDA'}

            # Add the learn task to the learning stage
            s3.add_tasks(t3)
            stages.append(s3)
        return stages


    def generate_interfacing_stage():
        s4 = Stage()
        s4.name = 'scanning'

        # Scaning for outliers and prepare the next stage of MDs
        t4 = Task()

        t4.pre_exec  = ['. /sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh || true']
        t4.pre_exec += ['conda activate %s' % cfg['conda_pytorch']]
        t4.pre_exec += ['mkdir -p %s/Outlier_search/outlier_pdbs' % cfg['base_path']]
        t4.pre_exec += ['export models=""; for i in `ls -d %s/CVAE_exps/model-cvae_runs*/`; do if [ "$models" != "" ]; then    models=$models","$i; else models=$i; fi; done;cat /dev/null' % cfg['base_path']]
        t4.pre_exec += ['export LANG=en_US.utf-8', 'export LC_ALL=en_US.utf-8']
        t4.pre_exec += ['unset CUDA_VISIBLE_DEVICES', 'export OMP_NUM_THREADS=4']

        cmd_cat = 'cat /dev/null'
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
                        '--n_outliers', 500,
                        '--dim1', cfg['residues'],
                        '--dim2', cfg['residues'],
                        '--cm_format', 'sparse-concat',
                        '--batch_size', cfg['batch_size'],
                        '--distributed']

        t4.cpu_reqs = {'processes'          : 6 * cfg['node_counts'],
                       'process_type'       : 'MPI',
                       'threads_per_process': 6 * 4,
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
        s1 = generate_MD_stage(num_MD=cfg['md_counts'])
        # Add simulating stage to the training pipeline
        p.add_stages(s1)

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
            'gpus'    : cfg['node_counts'] * cfg['gpu_per_node']
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
