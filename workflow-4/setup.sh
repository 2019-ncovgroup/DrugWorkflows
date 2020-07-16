. /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
conda create -n wf4 python=3.7 -y
conda activate wf4
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade

export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERNAME=litan
export RMQ_PASSWORD=sccDg7PxE3UjhA5L
export RADICAL_PILOT_DBURL="mongodb://litan:sccDg7PxE3UjhA5L@129.114.17.185:27017/rct-test"
