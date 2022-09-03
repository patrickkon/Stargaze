#!/bin/bash
set -e

cat << EOF > /etc/yum.repos.d/docker-ce.repo
[docker-ce-stable]
name=Docker CE Stable - x86_64
baseurl=https://download.docker.com/linux/centos/7/x86_64/stable
enabled=1
gpgcheck=1
gpgkey=https://download.docker.com/linux/centos/gpg
exclude=docker*
EOF

cat << EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg \
       https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
exclude=kube*
EOF

mkdir -p /etc/docker
cat <<EOF > /etc/docker/daemon.json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

cat << EOF > /etc/sysctl.d/kubernetes.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

yum install -y device-mapper-persistent-data lvm2 \
    kubelet kubeadm kubectl docker-ce-18.06.2.ce \
    --disableexcludes=kubernetes,docker-ce-stable

systemctl daemon-reload
systemctl restart docker
systemctl enable docker.service
systemctl enable --now kubelet

setenforce 0
sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config

modprobe br_netfilter
sysctl --system

swapoff -a
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

yum install -y unzip
yum install -y wget

# Install go
wget https://storage.googleapis.com/golang/getgo/installer_linux
chmod +x ./installer_linux
./installer_linux
source ~/.bash_profile

# Download cri-dockerd
# Instruction: https://kubernetes.io/docs/setup/production-environment/container-runtimes/#mcr
# Instructions: https://computingforgeeks.com/install-mirantis-cri-dockerd-as-docker-engine-shim-for-kubernetes/
wget https://github.com/Mirantis/cri-dockerd/archive/refs/tags/v0.2.0.zip
unzip v0.2.0.zip
cd cri-dockerd-0.2.0
mkdir bin
cd src && go get && go build -o ../bin/cri-dockerd
cd ..
mkdir -p /usr/local/bin
install -o root -g root -m 0755 bin/cri-dockerd /usr/local/bin/cri-dockerd
cp -a packaging/systemd/* /etc/systemd/system
sed -i -e 's,/usr/bin/cri-dockerd,/usr/local/bin/cri-dockerd,' /etc/systemd/system/cri-docker.service
systemctl daemon-reload
systemctl enable cri-docker.service
systemctl enable --now cri-docker.socket

# Activate NTP time sync:
yum install ntp -y
systemctl start ntpd.service
systemctl enable ntpd.service

# Other convenience packages:
yum install -y iperf3
yum install -y epel-release # for install stress
yum install -y stress # Command being used for now: stress -c 4 -t 15
yum install -y net-tools
yum install -y bridge-utils # for cni plugin
yum install -y jq # for cni plugin
yum install -y nmap # for cni plugin
yum install -y iftop
yum install -y hping3

# Enable IP packet forwarding: (note currently does not survive reboot)
sysctl -w net.ipv4.ip_forward=1
iptables --policy FORWARD ACCEPT
iptables-save

# Other commands:
mkdir ~/.kube