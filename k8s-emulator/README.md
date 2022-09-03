<!-- Purpose: for testing multi interface custom-routing vm connectivity in a k8s cluster, with our own CNI -->
# Kubernetes-based LEO Constellation Emulator

Our current implementation of the emulator uses familiar COTS software components, including k8s (with a custom bare-bones CNI), vagrant, KVM (libvirt), and Linux TC, among other tools. This is by no means a definitive solution, and we expect Stargaze or other new LEO emulators, to readily adopt other combinations of software components that suit their particular needs. 

# Usage and getting started
## Provide a constellation configuration script
- This essentially consists of 3 files: topos/<topo-filename>.txt, cluster_config.yaml and mapping/<mapping-filename>.txt. 
- Refer below for a formatting guide for the former 2 files. You can refer to the existing files as-is to reference too.

## Setup
```bash
# Setup host dependencies (Only needs to be run once for a given host for setup):
sh setup_host.sh

# Activate the appropriate conda environment (ensure this is activated every time the program is run):
conda activate stargaze-env
```

## Run the provided convenience scripts
```bash
# This will setup the k8s cluster complete with all requirements.
# Note: internally this is called before vagrant up.
# Note: this sets up kubectl on the client (host machine) too
# Values obtained from cluster_config.yaml
# Example: sh setup.sh 36000 60
sh setup.sh $DURATION $TIMESTEP

## Create this pod on all nodes beforehand:
kubectl apply -f kubernetes/get-statistics-daemonset.yaml

# Run this after the cluster has started (according to Vagrant output)
# This will activate latency and bandwidth shaping of links at each time step as configured in cluster_config.yaml
# Note: internally this will activate the systemd service in each VM in turn. 
bash start_tc.sh

# Run workload tests and collect metrics: 
python tests/workloads/ray/train_fashion_mnist/execute_train_fashion_mnist.py

# Collecting metrics (for your own custom workloads):
## Run this command during the start and at the end of the job you would like to measure/obtain statistics from:
python utils/measure_traffic.py
```

## (Optional) Deploy your own Ray cluster within the LEO constellation
Note: conda activate stargaze-env before running ray jobs. 
```bash
# Install a small Ray cluster with the default configuration, on Stargaze
helm -n ray install example-cluster --create-namespace ray/deploy/charts/ray

# SECTION: Inspect state:
kubectl -n ray get rayclusters
kubectl -n ray get pods
kubectl -n ray get service
kubectl get deployment ray-operator
kubectl get pod -l cluster.ray.io/component=operator
kubectl get crd rayclusters.cluster.ray.io

# Execute a job on the Ray cluster:
kubectl -n ray port-forward service/example-cluster-ray-head 10001:10001
## In a separate shell, run:
python ray/doc/kubernetes/example_scripts/run_local_example.py

# Clean-up by removing the Ray cluster:
kubectl -n ray delete raycluster example-cluster
helm -n ray uninstall example-cluster
```

### Format of topo.txt:
- Refer to topo_example.txt for an example.
- Assumptions: (1) all links are bidirectional. (2) connected graph. (3) GS-GS link does not exist
- Master nodes format: master node integer index prefixed with "m". e.g. m0 represents the first master node.
- Ground station nodes format: ground station node integer index prefixed with "g". e.g. g0 represents the first ground station node.
- Worker nodes format: integer index.
- Dummy nodes format: dummy node integer index prefixed with "d". e.g. d represents the first dummmy node.
- Only specify a single direction of the link, in the following order:
    - on the left part of each link: master nodes in ascending order, followed by worker nodes and dummy nodes in ascending order, followed by ground stations in ascending order.
    - on the right part of each link: an index which is larger than the left part  

### Format of cluster_config.yaml
- node_to_sat_or_gs_mapping_file: empty string or file_name
- init_isl_topo: string, currently choose one from [isls_plus_grid, isls_motif, isls_line]. initial ISL topology of the constellation. A corresponding ISL generation function must be defined in isls/ directory.
- pod_network, pod_subnet, node_network must have the following format: \*.\*.0.0/*
- timestep_granularity: integer value. Interpreted as seconds.
- simulation_time: integer value. Interpreted as seconds.
- num_gs: integer value. Number of ground stations.
- num_masters: integer value. Number of k8s master nodes.
- num_workers: integer value. Number of k8s worker nodes.
- num_isls: integer value. Represents the max ISLs per node that is permitted. This will be used for validation while evaluating certain functions.
- main_gs: choose one from [Paris, Moskva-(Moscow)]. Represents the initial ground station wherein the physically closest satellites in the given satellite constellation will be used as the nodes of our k8s cluster.
-  destination_gs: empty string, or choose one from [Paris, Moskva-(Moscow)].
- main_node: string value of a node in topo.txt. Represents the node that will be assigned to the physically closest satellite in the given satellite constellation. This affects the satellites that will be chosen to represent the nodes, which is dictatated by topo.txt. 
- constellation_name: choose one from [Starlink-550]. Represents the superset of the satellites used to represent the nodes.
- cpus (integer): vCPU count. This is pinned to distinct CPUs, please ensure no overprovisioning for accurate result reproduction. 
- memory (integer): Interpreted in MB.  
- gs_cpus (integer): same as cpus, but for the gs VMs.
- gs_memory (integer): same as memory, but for the gs VMs.
- isl_bandwidth: intger. ISL link bandwidth. Interpreted in Gbits.  
- gs_bandwidth: integer. GS-Sat link bandwidth. Interpreted in Gbits.

<!-- ## Other Notes
- systemd: this is used for the timer that activates our automated tc service -->

<!-- # Steps:
1. Ensure config files are properly populated: cluster_config.yaml, Vagrantfile (note this will be automated in future too).
2. Run the following: -->


<!-- 
# ISL runtime reconfiguration:
# Values obtained from cluster_config.yaml
# Example: sh utils/reconfig.sh 36000 60
sh utils/reconfig.sh $DURATION $TIMESTEP -->


<!-- # CSET evaluation scenarios:
sh tests/workloads/cset/link_expansion_scenario.sh
sh tests/workloads/cset/rerouting_scenario.sh -->

<!-- ## For testing all workloads:
### Step 1:
conda activate k8s-ray-test-env
### Step 2: ensure cluster_config.yaml refers to your intended constellation and master placement. if not, pull from ./cluster_config/
### Step 3: create k8s and ray cluster:
sh setup.sh 36000 60
### Step 4: Manually modify the workloads/**/execute_*.py files by updating the statistics_pod_list array.
### Step 4.5:
bash start_tc.sh
### Step 5: (Ray head mid)
sh run_all_tests.sh >> output_all_tests_motif_center_m_starlink_550_200_200_side_head.txt
### Step 6: (Ray head side) Modify /home/patkon/Stargaze/k8s-vagrant-libvirt/ray_related/deploy/charts/ray/values.yaml -> rayHeadType.nodeName to follow a side placement according to the topology. 
### Step 7: delete ray cluster and rerun tests. 
- Make sure final command in tests_temp.sh refers will redirect to correct file
sh tests_temp.sh
### Step 8: repeat the test
sh tests_temp.sh
### Step 9: 
vagrant destroy -f
``` -->

<!-- ### Creating a new constellation mapping and/or a new k8s node topology:
```bash
# Step 1: 
Get required satellite ID positions. Generate desired custom constellation in visualize_path.py
# Step 2:
Create desired topos in topos/
# Step 3: 
Create desired sat ID to node (step 2) mapping in mapping/
# Step 4: 
Modify cluster_config.yaml fields: topo_file, node_to_sat_or_gs_mapping_file, constellation_name.
# Step 5:
Run setup.sh (or all commands except vagrant up) to see all tc and routing configs
``` -->