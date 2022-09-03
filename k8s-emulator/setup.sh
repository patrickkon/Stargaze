#!/bin/bash

# Generate constellation data to be consumed by provision_tc_mod.py
# TODO: automate this. Currently users have to either use the default values (i.e. do not provide arguments to main.sh),
# or manually add them here (i.e. main.sh [duration] [timestep]) according to what they already defined in cluster_config.yaml
duration=$1 #seconds. make sure matches value in cluster_config.yaml
timestep=$2 #seconds. make sure matches value in cluster_config.yaml
timestep=$(($timestep * 1000)) # convert to milliseconds
bash -c "cd ../hypatia_plus; bash main.sh ${duration} ${timestep}"

# Config:
python3 utils/provision_routes.py 0
python3 utils/provision_tc_mod.py

# Create cluster:
vagrant up

# Just for generating test results faster (remove this later): (make sure conda activate is in the right environment already)
# conda activate k8s-ray-test-env
vagrant ssh m0 -c "sudo cat /etc/kubernetes/admin.conf" > ~/.kube/config
# Manually add: cordon all gs and dummy nodes
kubectl cordon g0
kubectl cordon g1
kubectl cordon g2
kubectl cordon d0
kubectl cordon d1
kubectl apply -f kubernetes/get-statistics-daemonset.yaml
kubectl apply -f kubernetes/isl_reconfig/isl_reconfig_daemonset.yaml
# helm -n ray install example-cluster --create-namespace ../../ray_related/deploy/charts/ray
# sleep 5m