# Deploy W2 on Summit

## SSH to Summit Login nodes

```
ssh $USER@summit.olcf.ornl.gov
```

## Deploy RCT 

```
. "/sw/summit/python/3.6/anaconda3/5.3.0/etc/profile.d/conda.sh"
conda activate WF2 || conda create -y -n WF2
pip install radical.entk

```

## Deploy W2 repository

```
cd $MEMBERWORK/med110
git clone --single-branch --branch wf2/molecules https://github.com/2019-ncovgroup/DrugWorkflows.git  
```
