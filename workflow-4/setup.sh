. /ccs/home/litan/miniconda3/etc/profile.d/conda.sh
conda create -n wf4 python=3.7 -y
conda activate wf4
pip install radical.entk radical.pilot radical.saga radical.utils --upgrade

export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERNAME=<your username>
export RMQ_PASSWORD=<your password>
export RADICAL_PILOT_DBURL="mongodb://<your username>:<your password>@129.114.17.185:27017/rct-test"
