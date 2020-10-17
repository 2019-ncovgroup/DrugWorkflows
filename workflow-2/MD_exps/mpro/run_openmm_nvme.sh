####
echo wrapper start
date

nvme=true
orgpath=`pwd`
omm_dirname=$(basename $orgpath)
if [ "$nvme" != "" ]
then
	BBPATH=/mnt/bb/$USER/
	mkdir -p $BBPATH/$omm_dirname
	echo "mkdir -p $BBPATH/$omm_dirname"
	output_path=$BBPATH/$omm_dirname
	cd $output_path
fi

####
echo md is ready
date

#python_path='/ccs/home/hrlee/.conda/envs/workflow-3/bin/python'
#md_invocation="$python_path /gpfs/alpine/scratch/hrlee/med110/git/2019-ncovgroup/DrugWorkflows/workflow-2/MD_exps/3clpro/run_openmm.py --topol /gpfs/alpine/scratch/hrlee/med110/git/2019-ncovgroup/DrugWorkflows/workflow-2/Parameters/input_protein/prot.prmtop --pdb_file /gpfs/alpine/scratch/hrlee/med110/git/2019-ncovgroup/DrugWorkflows/workflow-2/Parameters/input_protein/prot.pdb --length 100"

md_invocation=$@
($md_invocation)

####
echo md is done
date

if [ "$nvme" != "" ]
then
	echo cp $output_path/* $orgpath
	cp $output_path/* $orgpath
	####
	echo copy is done
	date
fi
