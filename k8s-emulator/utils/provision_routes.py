# Goal: fill in 3 files for each node within the bash-cni-plugin folder: 10-bash-cni-plugin.conf, setup_cni.sh, setup_route.sh
import yaml
import sys
import os
import shutil
from collections import defaultdict

def get_config_yaml_dict(filename):
    with open(filename, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(exc)

def get_setup_cni_template(pod_subnet, node_name, pod_ip_route_string):
    cni_ip = pod_subnet.split("/")[0][:-1] + "1/24"
    s = '''mkdir -p /etc/cni/net.d/
mv /vagrant/bash-cni-plugin/{}/10-bash-cni-plugin.conf /etc/cni/net.d/

mv /vagrant/bash-cni-plugin/bash-cni /opt/cni/bin/

sudo brctl addbr cni0
sudo ip link set cni0 up
sudo ip addr add {} dev cni0

# Allow inter-pod communication within this VM. This is actually redundant since in the Vagrantfile I already specified to ACCEPT all FORWARD chains within the filter table of iptables. 
sudo iptables -t filter -A FORWARD -s {} -j ACCEPT
sudo iptables -t filter -A FORWARD -d {} -j ACCEPT

# Allow inter-pod communication across all VMs in our cluster
{}'''.format(node_name, cni_ip, pod_subnet, pod_subnet, pod_ip_route_string)

    return s

def get_cni_plugin_template(pod_network, pod_subnet):
    # double braces e.g. {{ to inform python not to substitute with placeholder in format
    s = '''{{
    "cniVersion": "0.3.1",
    "name": "mynet",
    "type": "bash-cni",
    "network": "{}",
    "subnet": "{}"
}}'''.format(pod_network, pod_subnet)

    return s

CLUSTER_CONFIG_FILE = "cluster_config.yaml"
CLUSTER_CONFIG = get_config_yaml_dict(CLUSTER_CONFIG_FILE)

SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt"
SATS_TOPO_WITH_INTERFACE_AND_IP_FILE = "gen_cluster_data/topo_with_interface_and_ip_file.txt"

def node_string_to_int(CLUSTER_CONFIG, node):
    NUM_MASTERS = CLUSTER_CONFIG["num_masters"]
    NUM_WORKERS = CLUSTER_CONFIG["num_workers"]
    NUM_GS = CLUSTER_CONFIG["num_gs"]
    if "m" in node: # this is a master node:
        return int(node.split('m')[1])
    elif "g" in node:
        return int(node.split('g')[1]) + NUM_MASTERS + NUM_WORKERS
    elif "d" in node:
        return int(node.split('d')[1]) + NUM_MASTERS + NUM_WORKERS + NUM_GS
    else: # this is a worker node
        return int(node) + NUM_MASTERS

def node_int_to_string(CLUSTER_CONFIG, node):
    NUM_MASTERS = CLUSTER_CONFIG["num_masters"]
    NUM_WORKERS = CLUSTER_CONFIG["num_workers"]
    NUM_GS = CLUSTER_CONFIG["num_gs"]
    if node < NUM_MASTERS: # if src is a master node
        src_string = "m" + str(node)
    elif node < NUM_MASTERS + NUM_WORKERS: # if src is a worker node
        src_string = str(node - NUM_MASTERS)
    elif node < NUM_MASTERS + NUM_WORKERS + NUM_GS: # if src is a gs
        src_string = "g" + str(node - NUM_MASTERS - NUM_WORKERS)
    else: # if src is a dummy node
        src_string = "d" + str(node - NUM_MASTERS - NUM_WORKERS - NUM_GS)
    return src_string

# append interface name to satellites based on link
def add_int_sat(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_FILE):
    SATS_TOPO_FILE = CLUSTER_CONFIG["topo_file"]

    with open(SATS_TOPO_WITH_INTERFACE_FILE, 'w') as updated_topos:
        node_interfaces = {} # the value of each key (representing a VM) indicates the latest occupied interface with prefix eth.
        with open(SATS_TOPO_FILE, 'r') as topos:
            for topo in topos:
                row = topo.split()
                assert len(row) == 2
                if row[0] not in node_interfaces:
                    # first interface occupied by VMs dedicated for the k8s cluster is eth1. Since vagrant is using eth0
                    node_interfaces[row[0]] = 1
                else:
                    node_interfaces[row[0]] += 1
                if row[1] not in node_interfaces:
                    # first interface occupied by VMs dedicated for the k8s cluster is eth1. Since vagrant is using eth0
                    node_interfaces[row[1]] = 1
                else:
                    node_interfaces[row[1]] += 1
                new_row = "{} eth{} {} eth{}\n".format(row[0], node_interfaces[row[0]], row[1], node_interfaces[row[1]]) 
                updated_topos.write(new_row)

def add_vm_int_ip(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_FILE, SATS_TOPO_WITH_INTERFACE_AND_IP_FILE):
    """Assign IP addresses to each VMs interfaces that are involved in pod networking:
    NOTE: Currently max num of links is 255. This is because we use a 16 bit routing prefix. Leaving 8 bits for each link, and 8 further bits (though only 2 values are ever used) as the end points of the link.
    this could definitely amended in future.

        Parameters:
            CLUSTER_CONFIG: read-only. provided k8s cluster config yaml filename.
            SATS_TOPO_WITH_INTERFACE_FILE: read-only. 
            SATS_TOPO_WITH_INTERFACE_AND_IP_FILE: our output side-effect. 

        Returns: 

    """
    node_network_subnet = CLUSTER_CONFIG["node_network"]
    
    assert node_network_subnet.split("/")[1] == "16"

    node_network_subnet = node_network_subnet.split("/")[0]

    assert node_network_subnet.split('.')[2] == "0" and node_network_subnet.split('.')[3] == "0"

    def get_subnet_string(val1, val2):
        n = node_network_subnet.split('.')
        return "{}.{}.{}.{}/24".format(n[0], n[1], val1, val2)
    
    val1 = 1
    val2 = 2
    subnet_string = get_subnet_string(val1, val2)
    with open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'w') as updated_topos:
        with open(SATS_TOPO_WITH_INTERFACE_FILE, 'r') as topos:
            for topo in topos:
                assert val1 <= 255 and val2 <= 255
                row = topo.split()
                assert len(row) == 4
                
                # writing the IP for each end point of the current link
                new_row = "{} {} {} {} {} {}\n".format(row[0], row[1], get_subnet_string(val1, val2), row[2], row[3], get_subnet_string(val1, val2+1)) 
                updated_topos.write(new_row)

                val1 += 1

def add_all_node_ip_route(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, is_isl_reconfig):
    """ Use shortest paths routing to determine static routing tables for all nodes. Set all files in bash-cni-plugin for all nodes
    """
    CNI_DIR = CLUSTER_CONFIG["cni_dir"]
    NUM_MASTERS = CLUSTER_CONFIG["num_masters"]
    NUM_WORKERS = CLUSTER_CONFIG["num_workers"]

    # Format: {node0: [(node1, node0 interface, ip of node1 interface)]}. We use this to store links, in this example, node0-node1 is a link
    graph = defaultdict(list)

    num_edges = 0 # note: bidirectional link counts as 1
    subnet_prefix = CLUSTER_CONFIG["node_network"].split("0")[0]
    subnet_suffix = ".0/24"
    # Format: {"subnet_prefix + x + subnet_suffix": [(node0, node1, etc..)]}
    # Used when determining closest node to a given interface: which could be 1 of 2 end-nodes of the link
    interface_subnets = defaultdict(list) 

    with open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'r') as topos:
        for topo in topos:
            row = topo.split()
            num_edges += 1
            assert len(row) == 6
            # NOTE: we assume that all links are bidirectional, although topo.txt only specifies 1 direction of the link

            left = row[0]
            right = row[3]

            left = node_string_to_int(CLUSTER_CONFIG, left)
            right = node_string_to_int(CLUSTER_CONFIG, right)

            graph[left].append((right, row[1], row[5]))
            graph[right].append((left, row[4], row[2]))

            subnet = subnet_prefix + str(num_edges) + subnet_suffix
            interface_subnets[subnet].append((left, right))

        num_vertices = len(graph.keys())
    print(graph)
    for src in range(num_vertices):
        print(src, num_vertices, graph)
        next_hop_list, distance_list = all_next_hop(src, all_dst_bfs(src, graph, num_vertices), num_vertices)
        src_string = node_int_to_string(CLUSTER_CONFIG, src)

        SETUP_ROUTE_DIR = CNI_DIR + "/" + src_string
        ROUTE_LIST_FILE = SETUP_ROUTE_DIR + "/route_list.txt" # this file merely serves as an archive
        SETUP_ROUTE_FILE = SETUP_ROUTE_DIR + "/setup_route.sh"
        CNI_PLUGIN_FILE = SETUP_ROUTE_DIR + "/10-bash-cni-plugin.conf"
        SETUP_CNI_FILE = SETUP_ROUTE_DIR + "/setup_cni.sh"
        if os.path.exists(SETUP_ROUTE_DIR):
            # delete directory if it already exists
            shutil.rmtree(SETUP_ROUTE_DIR)
        os.makedirs(SETUP_ROUTE_DIR, exist_ok=True)

        # Format: {"dst node index": [(ip of dst node interface, src node interface)]}
        dst_store = defaultdict(list)

        if not is_isl_reconfig:
            # for each dst given this src, determine the next hop's IP and the src interface to reach that IP
            with open(ROUTE_LIST_FILE, 'w') as route_list_file:
                pod_subnet = CLUSTER_CONFIG['pod_subnet'].split("/")[0][:-3] + str(src) + ".0/24"
                pod_network = CLUSTER_CONFIG['pod_network']
                node_name = src_string
                pod_ip_route_string = ""

                # next hop represents the next hop node required to reach a dst (represented by index of next_hop_list)
                for index, next_hop in enumerate(next_hop_list):
                    dst_pod_subnet = CLUSTER_CONFIG['pod_subnet'].split("/")[0][:-3] + str(index) + ".0/24"
                    if next_hop == src:
                        continue
                    # get the interface and IP necessary to reach next hop, for this dst
                    for link in graph[src]:
                        if link[0] == next_hop:
                            dst_string = node_int_to_string(CLUSTER_CONFIG, index)

                            # Format: src, dst, next hop node interface IP, src interface to reach next hop
                            new_row = "{} {} {} {}\n".format(src_string, dst_string, link[2], link[1])
                            route_list_file.write(new_row)

                            new_row = "ip route add {} via {} dev {}\n".format(dst_pod_subnet, link[2].split("/")[0], link[1])
                            pod_ip_route_string += new_row

                            dst_store[index].append((link[2], link[1]))
                            break
                
                # Section: write cni related files for given src node
                setup_cni_string = get_setup_cni_template(pod_subnet, node_name, pod_ip_route_string)
                cni_plugin_string = get_cni_plugin_template(pod_network, pod_subnet)
                with open(CNI_PLUGIN_FILE, "w") as cni_plugin_file, open(SETUP_CNI_FILE, "w") as setup_cni_file:
                    cni_plugin_file.write(cni_plugin_string)
                    setup_cni_file.write(setup_cni_string)

            assert len(dst_store.keys()) == num_vertices - 1
            # write "ip route add" for each node in the cluster:
            with open(SETUP_ROUTE_FILE, 'w') as setup_route_file:
                for k, i in interface_subnets.items():
                    left_node = i[0][0]
                    right_node = i[0][1]

                    # We do not need to add ip route for interfaces directly connected to our current src node
                    if left_node == src or right_node == src:
                        continue

                    # We choose the closer (by hop count) node to source, for routing to the given subnet 
                    if distance_list[left_node] <= distance_list[right_node]:
                        route_details = dst_store[left_node]
                    else:
                        route_details = dst_store[right_node]
                    
                    new_row = "ip route add {} via {} dev {}\n".format(k, route_details[0][0].split("/")[0], route_details[0][1])
                    setup_route_file.write(new_row)
        else:
            pass # todo later

def all_dst_bfs(src, graph, num_vertices):
    """Get shortest path to all nodes for a given src node

        Parameters:
            src (int)
            graph (defaultdict)
            num_vertices (int)

        Returns:
            parent_list: a list that allows us to traverse from each dst to the src, tracing the shortest path
    """
    visited = [False] * num_vertices
    parent_list = [-1] * num_vertices

    queue = []
    queue.append(src)
    visited[src] = True

    while False in visited:
        s = queue.pop(0)

        for i in graph[s]:
            if visited[i[0]] == False:
                queue.append(i[0])
                visited[i[0]] = True
                parent_list[i[0]] = s 
    return parent_list

def all_next_hop(src, parent_list, num_vertices):
    """Get next hop node, and total path distance for shortest paths to all nodes for a given src node.
    note that the parent_list obtained is associated with the src.

        Returns:
            next_hop_list (list): each index represents a destination node relative to the source node (src), and the value represents the next hop node index  
            distance_list (list): each value represents the number of hops required to reach any given index (destination). 
    """
    next_hop_list = [-1] * num_vertices # a value of -1 means the closest next hop is itself. 
    distance_list = [-1] * num_vertices 
    for index, dst in enumerate(parent_list):
        distance = 1
        if dst == -1:
            continue
        if dst == src:
            next_hop_list[index] = index
            distance_list[index] = distance
        parent = dst
        while parent != src:
            distance += 1
            old_parent =  parent
            parent = parent_list[parent]
            if parent == src:
                next_hop_list[index] = old_parent
                distance_list[index] = distance
                break

    return next_hop_list, distance_list

def get_graph(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, CLUSTER_CONFIG):
    """ Taken partially from def add_all_node_ip_route"""
    # Format: {node0: [(node1, node0 interface, ip of node1 interface)]}. We use this to store links, in this example, node0-node1 is a link
    graph = defaultdict(list)
    # print(graph)
    with open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'r') as topos:
        for topo in topos:
            # print(topo)
            row = topo.split()
            assert len(row) == 6
            # NOTE: we assume that all links are bidirectional, although topo.txt only specifies 1 direction of the link

            left = row[0]
            right = row[3]

            left = node_string_to_int(CLUSTER_CONFIG, left)
            right = node_string_to_int(CLUSTER_CONFIG, right)

            graph[left].append((right, row[1], row[5]))
            graph[right].append((left, row[4], row[2]))

    return graph

def replace_route_between_2_nodes(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, CLUSTER_CONFIG, BASE_DIR, node0, node1, node0_ip_subnet, node1_ip_subnet):
    """Given a SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, determine a route between 2 nodes (specifically 2 interfaces). For all nodes that require ip route modifications, delete existing routes to the 2 nodes before adding new routes.

        Note: this does not rewrite CNI paths at all. i.e. not supported for now.
        Note: this only works if the 2 nodes have a direct link (i.e. share a common subnet through some link)

        Parameters:
            node0: string, with "n" removed
            node1: string, with "n" removed
            node0_ip_subnet: string,
                example: 172.16.2.1/24
            node1_ip_subnet: string,
                example: 172.16.2.2/24
    """

    graph = get_graph(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, CLUSTER_CONFIG)

    node0 = node_string_to_int(CLUSTER_CONFIG, node0)
    node1 = node_string_to_int(CLUSTER_CONFIG, node1)

    return gen_replace_route_script(CLUSTER_CONFIG, graph, BASE_DIR, node0, node1, node0_ip_subnet, node1_ip_subnet)

def gen_replace_route_script(CLUSTER_CONFIG, graph, BASE_DIR, node0, node1, node0_ip_subnet, node1_ip_subnet):
    """
        Only works for the case where a link is removed and a new path needs to be constructed resulting from that link removal. The link is represented by node0_ip_subnet <-> node1_ip_subnet
        Assumption: node0 and node1 have already been converted by node_string_to_int
    """
    num_vertices = len(graph.keys())
    interface_subnets = defaultdict(list)
    node0_subnet_prefix = node0_ip_subnet.split("/")[0][:-2] 
    node1_subnet_prefix = node1_ip_subnet.split("/")[0][:-2] 
    subnet_suffix = ".0/24"
    node0_subnet = node0_subnet_prefix + subnet_suffix
    node1_subnet = node1_subnet_prefix + subnet_suffix

    assert node0_subnet == node1_subnet
    interface_subnets[node0_subnet].append((node0, node1))

    NODENAME_AND_SETUP_ROUTE_FILES = []

    def replace_one_way_direction(src, dst, dst_ip, NODENAME_AND_SETUP_ROUTE_FILES):
        while src != -1: # with each iteration, we get one hop closer from src to dst
            next_hop_list, distance_list = all_next_hop(src, all_dst_bfs(src, graph, num_vertices), num_vertices)
            src_string = node_int_to_string(CLUSTER_CONFIG, src)

            def corrected_node(src_string):
                if src_string.isdigit():
                    return "n" + src_string
                else:
                    return src_string
            nodename = corrected_node(src_string)

            SETUP_ROUTE_DIR = BASE_DIR + src_string
            SETUP_ROUTE_FILE = SETUP_ROUTE_DIR + "/setup_route.sh"
            called_before = False
            for i in NODENAME_AND_SETUP_ROUTE_FILES:
                if nodename == i[0]:
                    called_before = True
            if not called_before:
                if os.path.exists(SETUP_ROUTE_DIR):
                    # delete directory if it already exists
                    shutil.rmtree(SETUP_ROUTE_DIR)
                os.makedirs(SETUP_ROUTE_DIR, exist_ok=True)

            # Format: {"dst node index": [(ip of dst node interface, src node interface)]}
            dst_store = defaultdict(list)

            # for each dst given this src, determine the next hop's IP and the src interface to reach that IP
            # next hop represents the next hop node required to reach a dst (represented by index of next_hop_list)
            for index, next_hop in enumerate(next_hop_list):
                if next_hop == src:
                    continue
                # get the interface and IP necessary to reach next hop, for this dst
                for link in graph[src]:
                    if link[0] == next_hop:
                        dst_store[index].append((link[2], link[1]))
                        break
            assert len(dst_store.keys()) == num_vertices - 1

            src = next_hop_list[dst]
            if src == -1:
                break

            route_details = dst_store[dst]
            # print(route_details)
            next_hop_ip = route_details[0][0].split("/")[0]
            next_hop_int = route_details[0][1]

            # write "ip route add" for each node in the cluster:
            with open(SETUP_ROUTE_FILE, 'a') as setup_route_file:
                # Mandatory row for simulating ISL reconnection: (just a monkey patch for now. Place this in a higher level later for tidiness if needed):
                ISL_RESET_DELAY = 3 # Assume 3 second delay in resetting ISL connection
                new_row = "sleep {}\n".format(ISL_RESET_DELAY)
                setup_route_file.write(new_row)
                new_row = "ip route del {}\n".format(dst_ip)
                setup_route_file.write(new_row)
                new_row = "ip route add {} via {} dev {}\n".format(dst_ip, next_hop_ip, next_hop_int)
                setup_route_file.write(new_row)
                exists = False
                for files in NODENAME_AND_SETUP_ROUTE_FILES:
                    if nodename == files[0]:
                        exists = True
                if not exists:
                    NODENAME_AND_SETUP_ROUTE_FILES.append([nodename, SETUP_ROUTE_FILE])
        
        return NODENAME_AND_SETUP_ROUTE_FILES

    # Overwrite all nodes starting from node0, all the way just before node1 (i.e. next hop is node1), with a path to node1_ip_subnet:
    src = node0
    dst = node1
    dst_ip = node1_ip_subnet.split("/")[0] # we want the specific ip, not just the subnet
    replace_one_way_direction(src, dst, dst_ip, NODENAME_AND_SETUP_ROUTE_FILES)

    # Overwrite all nodes starting from node1, all the way just before node1 (i.e. next hop is node0), with a path to node0_ip_subnet:
    src = node1
    dst = node0
    dst_ip = node0_ip_subnet.split("/")[0] # we want the specific ip, not just the subnet
    replace_one_way_direction(src, dst, dst_ip, NODENAME_AND_SETUP_ROUTE_FILES)   

    return NODENAME_AND_SETUP_ROUTE_FILES
    # print(graph)
    # for src in range(num_vertices):
    #     # print(src, num_vertices)
    #     next_hop_list, distance_list = all_next_hop(src, all_dst_bfs(src, graph, num_vertices), num_vertices)
    #     src_string = node_int_to_string(CLUSTER_CONFIG, src)

    #     def corrected_node(src_string):
    #         if src_string.isdigit():
    #             return "n" + src_string
    #         else:
    #             return src_string
    #     nodename = corrected_node(src_string)

    #     SETUP_ROUTE_DIR = BASE_DIR + src_string
    #     SETUP_ROUTE_FILE = SETUP_ROUTE_DIR + "/setup_route.sh"
    #     if os.path.exists(SETUP_ROUTE_DIR):
    #         # delete directory if it already exists
    #         shutil.rmtree(SETUP_ROUTE_DIR)
    #     os.makedirs(SETUP_ROUTE_DIR, exist_ok=True)

    #     # Format: {"dst node index": [(ip of dst node interface, src node interface)]}
    #     dst_store = defaultdict(list)

    #     # for each dst given this src, determine the next hop's IP and the src interface to reach that IP
    #     # next hop represents the next hop node required to reach a dst (represented by index of next_hop_list)
    #     for index, next_hop in enumerate(next_hop_list):
    #         if next_hop == src:
    #             continue
    #         # get the interface and IP necessary to reach next hop, for this dst
    #         for link in graph[src]:
    #             if link[0] == next_hop:
    #                 dst_store[index].append((link[2], link[1]))
    #                 break
    #     assert len(dst_store.keys()) == num_vertices - 1

    #     # write "ip route add" for each node in the cluster:
    #     with open(SETUP_ROUTE_FILE, 'w') as setup_route_file:
    #         written = False
    #         for k, i in interface_subnets.items():
    #             left_node = i[0][0]
    #             right_node = i[0][1]

    #             # We do not need to add ip route for interfaces directly connected to our current src node
    #             if left_node == src or right_node == src:
    #                 continue

    #             # We only want to perform this replace operation for the subnet involving the node0 and node1:
    #             if not ((left_node == node0 and right_node == node1) or (left_node == node1 and right_node == node0)):
    #                 continue

    #             # We choose the closer (by hop count) node to source, for routing to the given subnet 
    #             if distance_list[left_node] <= distance_list[right_node]:
    #                 route_details = dst_store[left_node]
    #             else:
    #                 route_details = dst_store[right_node]

    #             new_row = "ip route del {}\n".format(k)
    #             setup_route_file.write(new_row)
    #             new_row = "ip route add {} via {} dev {}\n".format(k, route_details[0][0].split("/")[0], route_details[0][1])
    #             setup_route_file.write(new_row)
    #             written = True
    #         if written:
    #             NODENAME_AND_SETUP_ROUTE_FILES.append([nodename, SETUP_ROUTE_FILE])

    return NODENAME_AND_SETUP_ROUTE_FILES

def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Must supply exactly 1 arguments")
        print("Usage: python3 provision_routes.py [is-isl-reconfig]")
        print("Example python3 provision_routes.py 1")
        exit(1)
    else:
        is_isl_reconfig = int(args[0])

        add_int_sat(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_FILE)

        add_vm_int_ip(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_FILE, SATS_TOPO_WITH_INTERFACE_AND_IP_FILE)

        add_all_node_ip_route(CLUSTER_CONFIG, SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, is_isl_reconfig)

if __name__ == "__main__":
    main()


