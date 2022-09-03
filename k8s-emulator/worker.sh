#!/bin/bash
set -e

kubeadm join ${MASTER_IP}:6443 --token ${TOKEN} \
  --discovery-token-unsafe-skip-ca-verification \
  --cri-socket /run/cri-docker.sock