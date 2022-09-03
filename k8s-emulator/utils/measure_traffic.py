import subprocess
from collections import defaultdict

def exec_sh_command(cmd):
    # proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = subprocess.run(
    cmd,
    text=True, check=True,
    capture_output=True).stdout

    return output

def exec_sh_catch_error_command(cmd, pod_name, node):
    # proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        out = subprocess.run(cmd, text=True, check=True, capture_output=True)
        out.check_returncode()
        output = out.stdout
        return output
    except subprocess.CalledProcessError as e:
        print ("Warning: make sure pod {} on node {} actually exists. If it does, remove from statistics_pod_list lists since it is currently unreachable.".format(pod_name, node))
        return None

def get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE):
    """Currently, we only obtain usage for ISLs of all nodes, except for the master nodes (this is only because by default from k8s v1.6+, daemonsets do not schedule to master nodes by default). But this can be indirectly observed through links from nodes connected to the master (which will occur since a base assumption for us is a connected graph topology)   
    """
    # SECTION: get all interfaces (that form ISLs, or the GS-Sat link) of each node in the cluster
    nodes_interfaces = defaultdict(list)

    with open(SATS_TOPO_WITH_INTERFACE_FILE, 'r') as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 4
            
            node0 = row[0]
            node1 = row[2]
            interface0 = row[1]
            interface1 = row[3]

            # if "m" in node0 and "m" in node1: # ignore master nodes
            #     continue

            if "g" not in node0 and "d" not in node0 and "m" not in node0:
                node0 = "n" + node0
            nodes_interfaces[node0].append(interface0)

            if "g" not in node1 and "d" not in node1 and "m" not in node1:
                node1 = "n" + node1
            nodes_interfaces[node1].append(interface1)

    pod_belongs = defaultdict(str) # format: {"node name": "statistics pod that resides in this node"}
    for pod in statistics_pod_list:
        get_pod_details_cmd = ['kubectl', 'get', 'pod', pod, '-o', 'wide']
        o = exec_sh_command(get_pod_details_cmd)
        node_name = o.split("\n")[1].split()[6]
        pod_belongs[node_name] = pod
        # print (node_name)
    
    # By default: we also want to measure the traffic passing through vagrant's automatically occupied interface
    for _, interfaces in nodes_interfaces.items():
        interfaces.append("eth0")

    # SECTION: for each node, access the associated get-statistics pod (created via daemonset) and run get_traffic.sh
    output_list = [] # format: [["node_name", "interface_name", "bytes_out", "bytes_in"]]
    for node, interfaces in nodes_interfaces.items():
        # Note: manually inserted for now:
        # print(node)
        # print(pod_belongs[node])
        # print(interface)
        get_traffic_cmd = ['kubectl', 'exec', '--stdin', '--tty', pod_belongs[node], '--', '/bin/bash', 'root/get_traffic.sh']
        get_traffic_cmd.extend(interfaces)
        # print(get_traffic_cmd)
        # cmd = ['kubectl', 'get', 'nodes']
        o = exec_sh_catch_error_command(get_traffic_cmd, pod_belongs[node], node) # we catch the error, which might be that the node is unreachable which can occur with our tc implementation
        if o == None:
            continue
        time = exec_sh_command(['date']).split("\n")[0] # currently this is UTC time
        # Note: this format is obtained from get_traffic.sh:
        rows = o.split("\n")
        for row in rows[:-1]:
            # print(row)
            _interface = row.split()[0]
            _interface_bytes_in = row.split()[1]
            _interface_bytes_out = row.split()[2]
            _interfaces_pkts_in = row.split()[3]
            _interfaces_pkts_out = row.split()[4]

            output_list.append([node,
                _interface,
                _interface_bytes_in,
                _interface_bytes_out,
                _interfaces_pkts_in,
                _interfaces_pkts_out,
            ])
        # to_print_string = "At time: {}, node: {}, stats_pod: {}, int: {}, bytes_out: {}, bytes_in: {}".format(time, node, pod_belongs[node], interface, _interface_bytes_in, _interface_bytes_out)
        # print (to_print_string)

    return output_list

def get_interval_all_node_interface_usage(node_interface_usage_old, node_interface_usage_new):
    """ 
        Parameters:
            node_interface_usage_old: output of get_all_node_interface_usage function. Represents the total traffic up till now for each interface of each node. 
            node_interface_usage_new: output of get_all_node_interface_usage function. Represents the total traffic up till now for each interface of each node. 

        Returns:
            node_interface_usage_interval: 2d-list
                Represents the difference in the amount of traffic, of: node_interface_usage_new - node_interface_usage_old. Converted to megabits. 
            agg_total_traffic: float
                Represents the total amount of traffic across all interfaces during this interval.

    """
    # Assumptions: that both input parameters are lists with the same number of elements
    node_interface_usage_interval = [] # format: [["node_name", "interface_name", "total_bytes_out", "total_bytes_in"]]
    agg_total_traffic = 0.0
    for index, old in enumerate(node_interface_usage_old):
        node = old[0]
        interface = old[1]

        new = node_interface_usage_new[index]

        assert new[0] == node and new[1] == interface # to make sure we are comparing the same node's interface

        old_bytes_out = float(old[3])
        old_bytes_in = float(old[2])
        
        old_pkts_in = float(old[4])
        old_pkts_out = float(old[5])

        new_bytes_out = float(new[3])
        new_bytes_in = float(new[2])

        new_pkts_in = float(new[4])
        new_pkts_out = float(new[5])

        # Convert to kilobits
        # unit = 1024

        # Convert to megabits: 
        unit = 131072

        total_out = (new_bytes_out - old_bytes_out) / unit
        total_in = (new_bytes_in - old_bytes_in) / unit
        agg_total_traffic += total_out + total_in

        total_pkt_in = new_pkts_in - old_pkts_in
        total_pkt_out = new_pkts_out - old_pkts_out

        # print_string = "node: {}, int: {}, total_bytes_out: {}, total_bytes_in: {}".format(node, interface, total_out, total_in)
        # print(print_string)

        node_interface_usage_interval.append([node, interface, total_out, total_in, total_pkt_in, total_pkt_out])

    return node_interface_usage_interval, agg_total_traffic


# cmd = ['echo', 'I like potatos']
# proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# o, e = proc.communicate()

# print('Output: ' + o.decode('ascii'))
# print('Error: '  + e.decode('ascii'))
# print('code: ' + str(proc.returncode))


# At time: Sat Apr  2 14:28:21 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 27572074946, bytes_in: 23880052513
# At time: Sat Apr  2 14:28:22 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 28249683232, bytes_in: 23131640456
# At time: Sat Apr  2 14:28:22 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 126918606869, bytes_in: 125977482807
# At time: Sat Apr  2 14:28:22 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 125980096427, bytes_in: 126915998605
# [['n0', 'eth1', '27572074946', '23880052513'], ['n1', 'eth1', '28249683232', '23131640456'], ['n1', 'eth2', '126918606869', '125977482807'], ['n2', 'eth1', '125980096427', '126915998605']]

# At time: Sat Apr  2 14:30:50 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 37714749966, bytes_in: 33960632967
# At time: Sat Apr  2 14:30:51 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 38343314808, bytes_in: 33272926088
# At time: Sat Apr  2 14:30:51 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 126983125301, bytes_in: 125982971353
# At time: Sat Apr  2 14:30:51 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 125985588946, bytes_in: 126980513633
# [['n0', 'eth1', '37714749966', '33960632967'], ['n1', 'eth1', '38343314808', '33272926088'], ['n1', 'eth2', '126983125301', '125982971353'], ['n2', 'eth1', '125985588946', '126980513633']]

# At time: Sat Apr  2 14:33:08 CDT 2022, node: n0, stats_pod: get-statistics-8zmsx, int: eth1, bytes_out: 37721927634, bytes_in: 33966887922
# At time: Sat Apr  2 14:33:08 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth1, bytes_out: 38361731948, bytes_in: 33278522000
# At time: Sat Apr  2 14:33:09 CDT 2022, node: n1, stats_pod: get-statistics-zf5dj, int: eth2, bytes_out: 126991386202, bytes_in: 125987290769
# At time: Sat Apr  2 14:33:09 CDT 2022, node: n2, stats_pod: get-statistics-hf8q7, int: eth1, bytes_out: 125989912046, bytes_in: 126988771055
# [['n0', 'eth1', '37721927634', '33966887922'], ['n1', 'eth1', '38361731948', '33278522000'], ['n1', 'eth2', '126991386202', '125987290769'], ['n2', 'eth1', '125989912046', '126988771055']]

# 131072