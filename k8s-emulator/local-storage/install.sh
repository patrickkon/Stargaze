#!/bin/bash

kubectl --kubeconfig=/etc/kubernetes/admin.conf \
    create -f /tmp/local-storage-storageclass.yaml

kubectl --kubeconfig=/etc/kubernetes/admin.conf \
    create -f /tmp/local-storage-provisioner.yaml
