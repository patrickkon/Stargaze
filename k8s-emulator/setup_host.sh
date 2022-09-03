# Setup the host such that it can connect to the k8s cluster, and create Ray clusters and jobs. 

sh ./scripts/kubectl_command.sh

# Create and activate conda environment, and install python 3.7.7
wget -O temp.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh ./temp.sh
rm ./temp.sh
conda create --name stargaze-env python=3.7.7
conda activate stargaze-env

python3 -m pip install pyyaml
python3 -m pip install requests
bash ../hypatia_plus/hypatia_plus_install_dependencies.sh

sh ./scripts/setup_ray.sh