# From: https://docs.ray.io/en/latest/cluster/kubernetes.html
# Assumptions: this is run within the host of the k8s cluster

# Install helm3
bash scripts/get-helm-3.sh

# Clone ray git repo
git clone https://github.com/ray-project/ray.git

# Install Pip 
# sudo yum --enablerepo=extras install epel-release
# sudo yum -y install python-pip
# sudo python3 -m pip install --upgrade pip

# Install ray in this conda environment:
# sudo yum install gcc-c++ python3-devel
python3 -m pip install ray
