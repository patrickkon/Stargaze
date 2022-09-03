# Allow kubectl command to access cluster located in host, from the host. 

# Prerequisite: 
# - ensure k8s cluster is running via "vagrant status" command in parent dir. 

# Install kubectl in host: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
# Note: only download a v1.23 (or one minor version difference from that used in the cluster)
curl -LO https://dl.k8s.io/release/v1.23.0/bin/linux/amd64/kubectl
curl -LO https://dl.k8s.io/release/v1.23.0/bin/linux/amd64/kubectl.sha256
echo "$(<kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl kubectl.sha256
# Output kubectl version installed:
kubectl version --client --output=yaml    

# Obtain kubeconfig file necessary to access cluster from host: 
# In host:
mkdir ~/.kube
vagrant ssh m0 -c "sudo cat /etc/kubernetes/admin.conf" > ~/.kube/config
kubectl cordon g0
kubectl cordon g1
# In each GS:
mkdir ~/.kube
# In host transfer to all GS:
vagrant scp ~/.kube/config <node-name>:~/.kube/config
# ssh vagrant@172.16.3.3 -i /home/patkon/Stargaze/k8s-vagrant-libvirt/.vagrant/machines/n2/libvirt/private_key


echo "test kubectl connection: "
kubectl get nodes

echo "DONE"