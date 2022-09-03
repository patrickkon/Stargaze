# A monitoring process that collects traffic utilization from all nodes and runs regulating functions in response to said traffic
# Assumptions: interfaces in SATS_TOPO_WITH_INTERFACE_FILE is accurate/up-to-date.
# Assumptions: routes in setup_route.sh for all nodes are accurate.
from hashlib import new
import sys, requests, re
from collections import defaultdict
from abc import ABC, abstractmethod
import time
from threading import Event, Thread
from tokenize import String
sys.path.append("utils")
from measure_traffic import get_all_node_interface_usage, get_interval_all_node_interface_usage, exec_sh_command
from provision_routes import replace_route_between_2_nodes, CLUSTER_CONFIG

BASE_PATH = ""
SATS_TOPO_WITH_INTERFACE_FILE = BASE_PATH + "gen_cluster_data/topo_with_interface_file.txt"
SATS_TOPO_WITH_INTERFACE_AND_IP_FILE = BASE_PATH + "gen_cluster_data/topo_with_interface_and_ip_file.txt"
statistics_pod_list = ["get-statistics-7r4x7", "get-statistics-8dd58", "get-statistics-9dppt", "get-statistics-vwb24", "get-statistics-wgblg", "get-statistics-x4vx6", "get-statistics-zx4b7"] # includes pods in all nodes except for k8s master node

INTERVAL = 10 # Expressed in seconds. Sampling 
BANDWIDTH_THRESHOLD = 800 # Expressed in Mb
PACKET_THRESHOLD = 100000
ISL_RESET_DELAY = 3 # Assume 3 second delay in resetting ISL connection

EXEC_ONCE = 1

# class RepeatedTimer:

#     """Repeat `function` every `interval` seconds."""

#     def __init__(self, interval, function, *args, **kwargs):
#         self.interval = interval
#         self.function = function
#         self.args = args
#         self.kwargs = kwargs
#         self.start = time.time()
#         self.event = Event()
#         self.thread = Thread(target=self._target)
#         self.thread.start()

#     def _target(self):
#         while not self.event.wait(self._time):
#             self.function(*self.args, **self.kwargs)

#     @property
#     def _time(self):
#         return self.interval - ((time.time() - self.start) % self.interval)

#     def stop(self):
#         self.event.set()
#         self.thread.join()

class Detector(ABC):

    """An abstract class for implementing detection functions"""

    @abstractmethod
    def detect(self, node_interfaces_exceed_threshold_interval):
        pass

    @abstractmethod
    def correct(self, node_interface_exceed_threshold_interval):
        pass

def detect_and_correct(detector:Detector, node_interfaces_exceed_threshold_interval):
    
    """Entrypoint function for detect and correct functionality"""
    
    to_correct = detector.detect(node_interfaces_exceed_threshold_interval)
    if to_correct:
        detector.correct(node_interfaces_exceed_threshold_interval)

        if EXEC_ONCE:
            sys.exit()

class LinkExpansion(Detector):

    """
        Rudimentary ISL link expansion functionality
        Currently only tested for adding a single link only, that passes through 2 end nodes connected with a single link. We assume that the nodes have additional unused interfaces (which is often not the case in topologies like +grid), so we can get away with just adding a link directly.
        For multi link multi paths scenarios, we need to change our route update mechanism, e.g. using Quagga OSPF + some custom CNI that "follows" OSPF path changes.
        Routing update is not supported currently.
        Assumption: we do not fix routes for CNI, and thus we assume the generating flow is not k8s related (unless a pod is in the host network). 
        Assumption: we assume the "new" (duplicated) link was created at vm init time, but is currently in down state
    """

    def __init__(self, node0_eth0_ip, node1_eth0_ip):
        self.node_to_ip = get_node_ips()
        self.node0_eth0_ip = node0_eth0_ip
        self.node1_eth0_ip = node1_eth0_ip
 
    def detect(self, node_interfaces_exceed_threshold_interval):
        """
            Ensure there is a single link that has exceeded the threshold, and return it
            Assumptions: link to be expanded already exists but is in down state.

            Output:
                node_interface_exceed_threshold_interval: 2-d list
                    each elem of the list has this format: [node, interface, total_out, total_in]
        """
        return len(node_interfaces_exceed_threshold_interval) == 2
    
    def correct(self, node_interface_exceed_threshold_interval):
        """Add an additional ISL (network interface) to the 2 end nodes of the congested link"""

        # Plan v1: Create a custom script that modify routing tables on each of the 2 end nodes: (i) add a new interface on each of the two nodes with a common subnet (ii) this subnet number is retrieved by getting the next highest unique subnet, from SATS_TOPO_WITH_INTERFACE_AND_IP_FILE (iii) change the path between the 2 end nodes to use ECMP static route: get all routes (specfically IPs) that pass through current interface (i.e. the current single link), delete them, then add an ECMP route for all those IPs via the current interface and the new interface.
        # Updated. Plan v2: assume the new link is down. (i) turn up link on both nodes (ii) use v1's (iii)
        
        node_scripts = self.create_route_script(node_interface_exceed_threshold_interval)

        # Send POST req to ISL_reconfig API's upload and exec endpoints on each of the 2 end nodes, and pass in the custom script
        for nsc in node_scripts:
            files = [('file', open(nsc[1], 'rb'))]
            URL = nsc[0] + "/isl-reconfig/upload"
            r = requests.post(url = URL, files=files)
            data = r.json()
            print(data)
            # print(r.text)

            URL = nsc[0] + "/isl-reconfig/exec"
            r = requests.post(url = URL, files=files)
            data = r.json()
            print(data)
        time = exec_sh_command(['date']).split("\n")[0] # currently this is UTC time
        print("Detected and corrected at time: ", time)

        # Update SATS_TOPO_WITH_INTERFACE_FILE to reflect the addition of this new ISL link. (this ensures next iteration of traffic monitoring will capture this new interface)

    def create_route_script(self, node_interface_exceed_threshold_interval):
        """
            Parameters:
                node_interface_exceed_threshold_interval: 2-d list
                    each elem of the list has this format: [node, interface, total_out, total_in]
            Output:
                node_scripts: 2-d listf
                    each elem is of the format: [node_exec_ip, route_script_filename]
                    example: [http://192.168.121.58:81, setup_route.sh]
        """
        # # Retrieve subnet number:
        # left_interface, right_interface = self.get_next_subnet()
        print("Create script...")
        node_scripts = []
            
        # Get the 2 nodes involved for this link:
        def correct_nodename(nodename):
            if "n" in nodename:
                nodename = nodename.split("n")[1]
            return nodename
        node0 = node_interface_exceed_threshold_interval[0][0]
        node1 = node_interface_exceed_threshold_interval[1][0]
        node0 = correct_nodename(node0)
        node1 = correct_nodename(node1)

        # Get original ISLs:
        node0_isl_int = node_interface_exceed_threshold_interval[0][1]
        node1_isl_int = node_interface_exceed_threshold_interval[1][1]

        # Get the duplicate ISL to turn up: (we assume that at init, duplicate ISL turned down is +1 of its counterpart ISL)
        def increment_interface(interface):
            match = re.match(r"([a-z]+)([0-9]+)", interface)
            if match:
                items = match.groups()
                new_int = int(items[1]) + 1
                return items[0] + str(new_int)
        node0_new_isl_int = increment_interface(node_interface_exceed_threshold_interval[0][1])
        node1_new_isl_int = increment_interface(node_interface_exceed_threshold_interval[1][1])

        # Routing filename:
        def get_route_filename(BASE_PATH, nodename):
            # nodename = correct_nodename(nodename)
            return "{}bash-cni-plugin/{}/setup_route.sh".format(BASE_PATH, nodename)

        NODE0_ROUTE_FILENAME = get_route_filename(BASE_PATH, node0)
        NODE1_ROUTE_FILENAME = get_route_filename(BASE_PATH, node1)

        # Output new routing filename:
        OUTPUT_NODE0_ROUTE_FILENAME = "{}_setup_route.sh".format(node0)
        OUTPUT_NODE1_ROUTE_FILENAME = "{}_setup_route.sh".format(node1)

        # Get IP at the other end of the interface:
        node1_isl_ip = ""
        node0_isl_ip = ""
        node1_new_isl_ip = ""
        node0_new_isl_ip = ""
        with open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'r') as topos:
            for line in topos:
                row = line.split()
                if (row[0] == node0 and row[1] == node0_isl_int):
                    node1_isl_ip = row[5].split("/")[0]
                    node0_isl_ip = row[2].split("/")[0]
                elif (row[3] == node0 and row[4] == node0_isl_int):
                    node0_isl_ip = row[5].split("/")[0]
                    node1_isl_ip = row[2].split("/")[0]
                elif (row[0] == node0 and row[1] == node0_new_isl_int):
                    node1_new_isl_ip = row[5].split("/")[0]
                    node0_new_isl_ip = row[2].split("/")[0]
                elif (row[3] == node0 and row[4] == node0_new_isl_int):
                    node0_new_isl_ip = row[5].split("/")[0]
                    node1_new_isl_ip = row[2].split("/")[0]        

        def generate_script(node_isl_int, other_node_isl_ip, node_new_isl_int, other_node_new_isl_ip, node_route_filename, output_node_route_filename, node_eth0_ip):
            new_rows = []
            with open(node_route_filename, 'r') as file1: # We assume each line is of the form: "ip route add 172.16.1.0/24 via 172.16.4.3 dev eth1"

                # Simulate ISL reset delay. Set at the start of script, as rest of commands complete very quickly
                new_rows.append("sleep {}\n".format(ISL_RESET_DELAY))

                # Delete existing routes (hardcode for now) that pass through the other node
                for line in file1:
                    if node_isl_int in line:
                        new_line = re.sub('add', 'del', line)
                        new_rows.append(new_line)
                    
                # Turn up the dormant interface:
                new_line = "ip link set dev {} up\n".format(node_new_isl_int)
                new_rows.append(new_line)

                # Add ECMP route for the deleted routes above:
                for row in new_rows[1:-1]:
                    dest_ip = row.split()[3]
                    ECMP_TEMPLATE = "ip route add {} nexthop dev {} via {} weight 1 nexthop dev {} via {} weight 1\n".format(dest_ip, node_new_isl_int, other_node_new_isl_ip, node_isl_int, other_node_isl_ip)
                    new_rows.append(ECMP_TEMPLATE)
                    # Note: not sure if i need to add a route for the direct neighbour too?
            
            with open(output_node_route_filename, "w") as file1:
                for row in new_rows:
                    file1.write(row)
            
            node_script = [node_eth0_ip, output_node_route_filename]
            return node_script

        node_scripts.append(generate_script(node0_isl_int, node1_isl_ip, node0_new_isl_int, node1_new_isl_ip, NODE0_ROUTE_FILENAME, OUTPUT_NODE0_ROUTE_FILENAME, self.node0_eth0_ip))
        node_scripts.append(generate_script(node1_isl_int, node0_isl_ip, node1_new_isl_int, node0_new_isl_ip, NODE1_ROUTE_FILENAME, OUTPUT_NODE1_ROUTE_FILENAME, self.node1_eth0_ip))
        print("finish create script...")
        # Write and return node_scripts
        return node_scripts

        # def turn_up_interface(interface):
        #     command = ['']
        

    def get_next_subnet(self):
        """Not implemented for now."""
        with open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'r') as topos:
            for line in topos:
                pass
            last_line = line
            row = last_line.split()
            cur_left = row[2]
            cur_right = row[5]

            def increment_subnet(subnet):
                pass

        
    def get_next_bridge(self):
        """Not implemented for now"""


class Reroute(Detector):

    """
        Rudimentary reroute (for static routes) functionality
        Currently only tested for rerouting a single link only, that passes through 2 end nodes.
        For multi link multi paths scenarios, we need to change our route update mechanism, e.g. using Quagga OSPF + some custom CNI that "follows" OSPF path changes.
        Routing update is not supported currently.
        Assumption: we do not fix routes for CNI, and thus we assume the generating flow is not k8s related (unless a pod is in the host network). 
        Assumption: we assume there may be a "new" (duplicated) link that was created at vm init time for the LinkExpansion scenario, but is currently in down state.
    """

    def __init__(self, node0_eth0_ip, node1_eth0_ip):
        self.node_to_ip = get_node_ips()
        self.node0_eth0_ip = node0_eth0_ip
        self.node1_eth0_ip = node1_eth0_ip
 
    def detect(self, node_interfaces_exceed_threshold_interval):
        """
            Ensure there is a single link that has exceeded the threshold, and return it
            Assumptions: link to be expanded already exists but is in down state.

            Output:
                node_interface_exceed_threshold_interval: 2-d list
                    each elem of the list has this format: [node, interface, total_out, total_in]
        """
        return len(node_interfaces_exceed_threshold_interval) == 2
    
    def correct(self, node_interface_exceed_threshold_interval):
        """Reroute paths to a least utilized path at the current moment"""

        # Plan v1: Create a custom script that modify routing tables 
        
        node_scripts = self.create_route_script(node_interface_exceed_threshold_interval)
        print(node_scripts)
        # Send POST req to ISL_reconfig API's upload and exec endpoints on each of the 2 end nodes, and pass in the custom script
        for nsc in node_scripts:
            files = [('file', open(nsc[1], 'rb'))]
            URL = nsc[0] + "/isl-reconfig/upload"
            r = requests.post(url = URL, files=files)
            data = r.json()
            print(data)
            # print(r.text)

            URL = nsc[0] + "/isl-reconfig/exec"
            r = requests.post(url = URL, files=files)
            data = r.json()
            print(data)
        time = exec_sh_command(['date']).split("\n")[0] # currently this is UTC time
        print("Detected and corrected at time: ", time)

        # Update SATS_TOPO_WITH_INTERFACE_FILE to reflect the addition of this new ISL link. (this ensures next iteration of traffic monitoring will capture this new interface)

    def create_route_script(self, node_interface_exceed_threshold_interval):
        """
            Parameters:
                node_interface_exceed_threshold_interval: 2-d list
                    each elem of the list has this format: [node, interface, total_out, total_in]
            Output:
                node_scripts: 2-d listf
                    each elem is of the format: [node_exec_ip, route_script_filename]
                    example: [http://192.168.121.58:81, setup_route.sh]
        """
        # # Retrieve subnet number:
        # left_interface, right_interface = self.get_next_subnet()
        print("Create script...")
        node_scripts = []
        PORT = 81
        PROTOCOL = "http://"
        
        # Get the 2 nodes involved for this link:
        def correct_nodename(nodename):
            if "n" in nodename:
                nodename = nodename.split("n")[1]
            return nodename
        node0 = node_interface_exceed_threshold_interval[0][0]
        node1 = node_interface_exceed_threshold_interval[1][0]
        node0 = correct_nodename(node0)
        node1 = correct_nodename(node1)

        # Get original ISLs:
        node0_isl_int = node_interface_exceed_threshold_interval[0][1]
        node1_isl_int = node_interface_exceed_threshold_interval[1][1]

        node0_ip_subnet = ""
        node1_ip_subnet = ""

        # # Output new routing filename:
        # OUTPUT_NODE0_ROUTE_FILENAME = "{}_setup_route.sh".format(node0)
        # OUTPUT_NODE1_ROUTE_FILENAME = "{}_setup_route.sh".format(node1)      

        def generate_scripts(node0, node1):

            # Generate new SATS_TOPO_WITH_INTERFACE_AND_IP_FILE by removing the congested link:
            # (no longer true) # NOTE: this removes all links wherein the 2-end nodes are node0 and node1. Of course, it does not have to be implemented this way. We can just remove the single link specified by node0_isl_int and node1_isl_int
            NEW_SATS_TOPO_WITH_INTERFACE_AND_IP_FILE = BASE_PATH + "gen_cluster_data/new_reroute_topo_with_interface_and_ip_file.txt" # Will be used in calculating the shortest path graph later.
            with open(NEW_SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'w') as new_topos, open(SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, 'r') as topos:
                for line in topos:
                    # We want to skip the congested link. 
                    # print(line, node0, node1, node0_isl_int, node1_isl_int)
                    row = line.split()
                    left_node = row[0]
                    right_node = row[3]
                    left_int = row[1]
                    right_int = row[4]

                    # Get IP_subnet for the node and its given interface:
                    if (node0 == left_node and node0_isl_int == left_int):
                        node0_ip_subnet = row[2]
                    elif (node0 == right_node and node0_isl_int == right_int):
                        node0_ip_subnet = row[5]
                    if (node1 == left_node and node1_isl_int == left_int):
                        node1_ip_subnet = row[2]
                    elif (node1 == right_node and node1_isl_int == right_int):
                        node1_ip_subnet = row[5]

                    # This removes all links associated with node0 and node1:
                    # if (node0 == left_node and node1 == right_node) or (node0 == right_node and node1 == left_node):
                    #     continue
                    
                    # This only removes the single link:
                    if (node0 == left_node and node1 == right_node and node0_isl_int == left_int and node1_isl_int == right_int) or (node0 == right_node and node1 == left_node and node0_isl_int == right_int and node1_isl_int == left_int):
                        continue

                    # print(line)
                    new_topos.write(line)

            BASE_DIR = "tests/workloads/cset/"
            NODENAME_AND_SETUP_ROUTE_FILES = replace_route_between_2_nodes(NEW_SATS_TOPO_WITH_INTERFACE_AND_IP_FILE, CLUSTER_CONFIG, BASE_DIR, node0, node1, node0_ip_subnet, node1_ip_subnet)
            # print("NODENAME_AND_SETUP_ROUTE_FILES", NODENAME_AND_SETUP_ROUTE_FILES)
            # Get IP of eth0 for each node in the generated files:
            # nodename_to_ip = defaultdict(str)
            node_scripts = []
            # kubectl get pods -o jsonpath='{range .items[*]}{@.metadata.name}{" "}{@.status.podIP}{" "}{@.spec.nodeName}{"\n"}{end}'
            command = ['kubectl', 'get', 'nodes', '-o', "wide"]
            o = exec_sh_command(command)
            rows = o.split("\n")[1:]
            for row in rows[:-1]:
                # if "isl-reconfig-api" in row:
                line = row.split() # this can split across arbitrary number of spaces
                # print(line)
                ip_now = line[5]
                node_now = line[0]
                print(ip_now, node_now)
                for i in NODENAME_AND_SETUP_ROUTE_FILES:
                    if i[0] == node_now:
                        ip_adjusted = PROTOCOL + ip_now + ":{}".format(PORT)
                        node_scripts.append([ip_adjusted, i[1]])
            return node_scripts

        node_scripts = generate_scripts(node0, node1)
        print("finish create script...")
        # print(node_scripts)
        # Write and return node_scripts
        return node_scripts

def get_node_ips():
    """
        Outputs a dict that maps node names to the IPs of their eth0 interfaces.

        Output:
            node_to_ip: dict
    """
    node_to_ip = defaultdict(str)


    return node_to_ip


def get_interfaces_exceed_limit(PACKET_THRESHOLD, time_interval, node_interface_usage_interval):
    """
        Outputs all interfaces that have exceeded a given PACKET_THRESHOLD at this time_interval

        Parameters:
            PACKET_THRESHOLD: int
                threshold expressed as count

            node_interface_usage_interval: 2-d list
                Each elem is of the form: [node, interface, total_out, total_in]
                Each elem represents the node interface usage at this time_interval

        Output:
            node_interfaces_exceed_threshold_interval: 2-d list
                Same as node_interface_usage_interval input param
    """
    node_interfaces_exceed_threshold_interval = []
    for row in node_interface_usage_interval:
        if row[4] / time_interval > PACKET_THRESHOLD or row[5] / time_interval > PACKET_THRESHOLD:
            node_interfaces_exceed_threshold_interval.append(row)
    return node_interfaces_exceed_threshold_interval

def get_with_extra_interfaces_exceed_limit(node_interfaces_exceed_threshold_interval, SATS_TOPO_WITH_INTERFACE_FILE):
    """Only return node pairs (which together compose a link) that have backup links available
    
        Parameters:
            node_interfaces_exceed_threshold_interval: 2-d list
                Each elem is of the form: [node, interface, total_out, total_in]

        Output:
            nodes_with_extra_interfaces_exceed_threshold_interval: 2-d list:
                same format as node_interfaces_exceed_threshold_interval
    """
    
    nodes_interfaces = defaultdict(list) # {1: [[2, [1, eth2, 2, eth1]]]}
    nodes_with_extra_interfaces = [] # [[1, eth2, 2, eth1]]
    nodes_with_extra_interfaces_exceed_threshold_interval = []

    with open(SATS_TOPO_WITH_INTERFACE_FILE, 'r') as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 4
            
            node0 = row[0]
            node1 = row[2]
            interface0 = row[1]
            interface1 = row[3]

            if node0 in nodes_interfaces:
                found = False
                for elem in nodes_interfaces[node0]:
                    if elem[0] == node1:
                        nodes_with_extra_interfaces.append(elem[1])
                        found = True
                if not found:
                    nodes_interfaces[node0].append([node1, [node0, interface0, node1, interface1]])
            else:
                nodes_interfaces[node0].append([node1, [node0, interface0, node1, interface1]])

    def correct_nodename(nodename):
        if "n" in nodename:
            nodename = nodename.split("n")[1]
        return nodename
    
    for elem in node_interfaces_exceed_threshold_interval:
        node = correct_nodename(elem[0])
        interface = elem[1]
        bytes_out = elem[2]
        bytes_in = elem[3]
        for elem2 in nodes_with_extra_interfaces:
            if (node == elem2[0] and interface == elem2[1]) or (node == elem2[2] and interface == elem2[3]):
                nodes_with_extra_interfaces_exceed_threshold_interval.append(elem)
    
    return nodes_with_extra_interfaces_exceed_threshold_interval

def monitor(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE, defense_name, node0_eth0_ip, node1_eth0_ip):

    if defense_name == "link_expansion":
        defense = LinkExpansion(node0_eth0_ip, node1_eth0_ip)
    elif defense_name == "reroute":
        defense = Reroute(node0_eth0_ip, node1_eth0_ip)
    else:
        raise ValueError("Unknown defense.")
    node_interface_usage_old = get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)
    time_old = time.monotonic()
    while True: # Our loop current does not require more wait time, because get_all_node_interface_usage takes a long enough time.. (~3s to be exact)

        node_interface_usage_now = get_all_node_interface_usage(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)
        time_now = time.monotonic()
        # print(node_interface_usage_now)
        node_interface_usage_interval, agg_total_traffic = get_interval_all_node_interface_usage(node_interface_usage_old, node_interface_usage_now) # this takes very short amount of time
        print("node_interface_usage_interval: ", node_interface_usage_interval)
        # print("Aggregate network traffic during interval: {}".format(agg_total_traffic))
        time_interval = time_now - time_old
        node_interfaces_exceed_threshold_interval = get_interfaces_exceed_limit(PACKET_THRESHOLD, time_interval, node_interface_usage_interval)
        nodes_with_extra_interfaces_exceed_threshold_interval = get_with_extra_interfaces_exceed_limit(node_interfaces_exceed_threshold_interval, SATS_TOPO_WITH_INTERFACE_FILE)
        print("Time interval: ", time_interval)
        print("Nodes that exceeded PACKET_THRESHOLD: ", node_interfaces_exceed_threshold_interval)
        print("Nodes with extra interfaces that exceeded PACKET_THRESHOLD: ", nodes_with_extra_interfaces_exceed_threshold_interval)
        # Run desired detection function:
        detect_and_correct(defense, nodes_with_extra_interfaces_exceed_threshold_interval)

        # Prepare for next iteration:
        node_interface_usage_old = node_interface_usage_now
        time_old = time_now

def main():
    args = sys.argv[1:]
    if len(args) != 3:
        # Note: only first arg is actually necessary now. Others can be deleted, since I have automated the mapping of nodename to eth0 ip above
        print("Must supply a defense type and 2 node IPs")
        print("Usage: python3 monitor.py [defense] [nodeX_eth0_ip] [nodeY_eth0_ip]")
        print("Example python3 monitor.py link_expansion http://192.168.121.22:81 http://192.168.121.109:81") # Thus, we assume that the caller knows the congested link beforehand, since these 2 nodes refer to the 2 end nodes of the congested link
        print("Example python3 monitor.py reroute http://192.168.121.58:81 http://192.168.121.60:81") # Thus, we assume that the caller knows the congested link beforehand, since these 2 nodes refer to the 2 end nodes of the congested link
        exit(1)
    else:
        monitor(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE, args[0], args[1], args[2])

if __name__ == "__main__":
    main()




# start timer
# get_all_traffic(statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)
# timer = RepeatedTimer(INTERVAL, get_all_traffic, statistics_pod_list, SATS_TOPO_WITH_INTERFACE_FILE)

# stop timer
# timer.stop()