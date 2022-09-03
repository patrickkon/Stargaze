#!/bin/bash
set -e

# Note: CRI socket provided by https://kubernetes.io/docs/setup/production-environment/container-runtimes/#mcr, which was "/run/cri-dockerd.sock" is incorrect
# Use this to get the correct socket: "systemctl status cri-docker.socket" from https://computingforgeeks.com/install-mirantis-cri-dockerd-as-docker-engine-shim-for-kubernetes/
kubeadm config images pull --cri-socket /run/cri-docker.sock
kubeadm init --pod-network-cidr=10.244.0.0/16 \
        --token ${TOKEN} --apiserver-advertise-address=${MASTER_IP} \
        --cri-socket /run/cri-docker.sock
# Testing using host-gw instead of vxlan, hoping for near native inter-node pod-to-pod networking:
# wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
# sed 's/vxlan/host-gw/' -i kube-flannel.yml
# KUBECONFIG=/etc/kubernetes/admin.conf kubectl apply -f kube-flannel.yml
# rm kube-flannel.yml
# sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf taint node master node-role.kubernetes.io/master:NoSchedule-