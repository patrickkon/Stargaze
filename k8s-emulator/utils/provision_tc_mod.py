import yaml
import os
import math
from collections import defaultdict
import shutil

# Currently, each node has its own distinct tc_mod.service, config_tc_mod.sh and tc_mod.sh files (this is fine since we do not expect too many nodes to cause this file to overwhelm storage), but they share the same tc_mod.timer file

def get_config_yaml_dict(filename):
    with open(CLUSTER_CONFIG_FILE, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(exc)

CLUSTER_CONFIG_FILE = "cluster_config.yaml"
CLUSTER_CONFIG = get_config_yaml_dict(CLUSTER_CONFIG_FILE)
GEN_CLUSTER_DATA_DIR = "gen_cluster_data"
TC_MOD_TIMER_FILE = GEN_CLUSTER_DATA_DIR + "/tc_mod.timer"
SATS_TOPO_WITH_INTERFACE_FILE = "gen_cluster_data/topo_with_interface_file.txt" # an input file written in provision_routes.py
SHARED_VAGRANT_DIR = "/vagrant"
HYPATIA_PLUS_DIR = "../hypatia_plus"

def get_tc_mod_timer_template(timestep_granularity):
    """Get tc_mod.timer file contents

        Parameters:
            timestep_granularity (integers): in seconds.
    """
    s = '''[Unit]
Description=Activate automated tc every OnUnitActiveSec seconds
[Timer]
OnBootSec=10
OnUnitActiveSec={}
AccuracySec=10ms
[Install]
WantedBy=timers.target'''.format(timestep_granularity)

    return s

def get_tc_mod_service_template(filename):
    s = '''[Unit]
Description=Activate automated tc
[Service]
ExecStart={}'''.format(filename)

    return s

def get_tc_mod_template(filename, max_num_links):
    s = '''#!/bin/sh

CURRENT_TIME=$(date -u)
echo "Current time: ${{CURRENT_TIME}}" >> /var/log/tc_mod-service.log
PREV_NUM=$(sed '1q;d' /tmp/temp_tc_count_store.txt)
echo "Current count: ${{PREV_NUM}}" >> /var/log/tc_mod-service.log
NUM="$((PREV_NUM + {}))"
echo "Next count: ${{NUM}}" >> /var/log/tc_mod-service.log
sed -i '1s/.*/'$NUM'/' /tmp/temp_tc_count_store.txt
NUM="$((PREV_NUM + {} - 1))"
for i in $(seq ${{PREV_NUM}} ${{NUM}});
do
    content=$(sed ''$i'q;d' {})
    eval "$content"
    echo "Command ran: $content" >> /var/log/tc_mod-service.log
done'''.format(max_num_links, max_num_links, filename)

    return s

def get_config_tc_mod_template(service_filename, timer_filename, script_filename):
    s = '''#!/bin/bash

# NOTE: this will be called by the Vagrant provisioner, to move the files to the appropriate locations.
mv {} /etc/systemd/system/
mv {} /etc/systemd/system/

# Create required files used by the tc_mod.service
mv /vagrant/utils/temp_tc_count_store.txt /tmp/
touch /var/log/tc_mod-service.log
chmod 777 /var/log/tc_mod-service.log

chmod 777 {}'''.format(service_filename, timer_filename, script_filename)

    return s

def interface_down(interface_name):
    """ Returns a string that prepends iptables rules to required FORWARD, INPUT, OUTPUT Chains of the FILTER table, for the given interface_name
        Note: we do not use ip link set because that removes routing entries related to the interface. 
    """
    s = "sudo iptables -I FORWARD 1 -i {} -j DROP; sudo iptables -I FORWARD 1 -o {} -j DROP; sudo iptables -I INPUT 1 -i {} -j DROP; sudo iptables -I OUTPUT 1 -o {} -j DROP".format(interface_name, interface_name, interface_name, interface_name)
    return s

def interface_up(interface_name):
    """ Returns a string that 'Turns on' an interface that was previously 'turned off' via def interface_down
    """
    s = "sudo iptables -D FORWARD -i {} -j DROP; sudo iptables -D FORWARD -o {} -j DROP; sudo iptables -D INPUT -i {} -j DROP; sudo iptables -D OUTPUT -o {} -j DROP".format(interface_name, interface_name, interface_name, interface_name)
    return s

def set_tc_mod_timer(CLUSTER_CONFIG):
    # Note: expressed in seconds
    timestep_granularity = CLUSTER_CONFIG['timestep_granularity']

    with open(TC_MOD_TIMER_FILE, 'w') as tc_mod_timer_file:
        tc_mod_timer_file.write(get_tc_mod_timer_template(int(timestep_granularity)))

def set_tc_mod(CLUSTER_CONFIG):
    timestep_granularity = int(CLUSTER_CONFIG["timestep_granularity"])
    max_time = int(CLUSTER_CONFIG["simulation_time"])
    num_isls = int(CLUSTER_CONFIG["num_isls"])
    num_gs = int(CLUSTER_CONFIG["num_gs"])

    # Format: {node0: [(node1, node0 interface, "up"/"down"]]}. 
    # Explanation: node0-node is a link, node0 is the interface of that link from node0's side, this link is either up or down.
    graph = defaultdict(list)
    with open(SATS_TOPO_WITH_INTERFACE_FILE, 'r') as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 4
            node0 = row[0]
            interface0 = row[1]
            node1 = row[2]
            interface1 = row[3]
            graph[node0].append([node1, interface0, "up"])
            graph[node1].append([node0, interface1, "up"])
    
    # SECTION: Write tc_mod.service and tc_mod.sh for each node, and tc_mod_commands.txt for each node for all timesteps. 

    # if os.path.exists(GEN_CLUSTER_DATA_DIR):
    #     # delete directory if it already exists
    #     shutil.rmtree(GEN_CLUSTER_DATA_DIR)
    # os.makedirs(GEN_CLUSTER_NODE_DIR, exist_ok=True)

    for node, links in graph.items():
        GEN_CLUSTER_NODE_DIR = GEN_CLUSTER_DATA_DIR + "/" + node
        TC_MOD_SERVICE_FILE = GEN_CLUSTER_NODE_DIR + "/tc_mod.service"
        TC_MOD_FILE = GEN_CLUSTER_NODE_DIR + "/tc_mod.sh"
        TC_MOD_COMMANDS_FILE = GEN_CLUSTER_NODE_DIR + "/tc_mod_commands.txt"
        CONFIG_TC_MOD_FILE = GEN_CLUSTER_NODE_DIR + "/config_tc_mod.sh"
        current_time = 0

        if os.path.exists(GEN_CLUSTER_NODE_DIR):
            # delete directory if it already exists
            shutil.rmtree(GEN_CLUSTER_NODE_DIR)
        os.makedirs(GEN_CLUSTER_NODE_DIR, exist_ok=True)

        # delete_file_if_exists(TC_MOD_SERVICE_FILE) # This is unnecessary since we are always overwriting
        delete_file_if_exists(TC_MOD_COMMANDS_FILE)

        with open(TC_MOD_SERVICE_FILE, "w") as tc_mod_service_file:
            TC_MOD_FILE_ABS_PATH = SHARED_VAGRANT_DIR + "/" + TC_MOD_FILE
            tc_mod_service_file.write(get_tc_mod_service_template(TC_MOD_FILE_ABS_PATH))

        with open(TC_MOD_FILE, "w") as tc_mod_file:
            TC_MOD_COMMANDS_FILE_ABS_PATH = SHARED_VAGRANT_DIR + "/" + TC_MOD_COMMANDS_FILE
            tc_mod_file.write(get_tc_mod_template(TC_MOD_COMMANDS_FILE_ABS_PATH, num_isls + num_gs))

        with open(CONFIG_TC_MOD_FILE, "w") as config_tc_mod_file:
            TC_MOD_SERVICE_FILE_ABS_PATH = SHARED_VAGRANT_DIR + "/" + TC_MOD_SERVICE_FILE
            TC_MOD_TIMER_FILE_ABS_PATH = SHARED_VAGRANT_DIR + "/" + TC_MOD_TIMER_FILE
            TC_MOD_FILE_ABS_PATH = SHARED_VAGRANT_DIR + "/" + TC_MOD_FILE
            config_tc_mod_file.write(get_config_tc_mod_template(TC_MOD_SERVICE_FILE_ABS_PATH, TC_MOD_TIMER_FILE_ABS_PATH, TC_MOD_FILE_ABS_PATH))

        with open(TC_MOD_COMMANDS_FILE, "a") as tc_mod_commands_file:
            while current_time <= max_time:
                if "g" in node:
                    assert count_actual_isls(links, node) == 0
                else:
                    assert count_actual_isls(links, node) <= num_isls
                filler = num_isls + num_gs - len(links) # we want to ensure that for each timestep, the number of rows that need to be processed by tc_mod.sh is the same, i.e. the number of rows is num_isls + num_gs (because this represents the max num of links any sat can have) for each timestep. This simplifies the implementation of tc_mod.sh
                for link in links:
                    node1 = link[0]
                    interface0 = link[1]
                    distance = get_node_pair_distance(CLUSTER_CONFIG, node, node1, current_time) # expressed in meters, float, or NAN (for gs-sat link if not reachable).
                    if distance != "NAN":
                        latency = get_latency(distance) # expressed in ms, int.
                        if "g" in node or "g" in node1:
                            bandwidth_gb = CLUSTER_CONFIG["gs_bandwidth"]
                        else:
                            bandwidth_gb = CLUSTER_CONFIG["isl_bandwidth"]
                        link_prev_status = link[2] # either "up" or "down"
                        
                        netem_string = "sudo tc qdisc replace dev {} root netem delay {}ms rate {}Gbit\n".format(interface0, latency, bandwidth_gb) #note: gbit granularity now, but can be changed later.
                        if link_prev_status == "up":
                            new_row = netem_string
                        elif link_prev_status == "down": # previously "down" but now "up" since distance != "NAN"
                            new_row = interface_up(interface0) + "; " + netem_string
                            link[2] = "up"
                    else:
                        link_prev_status = link[2] # either "up" or "down"
                        if link_prev_status == "up": # previously "up" but now "down" since distance == "NAN"
                            new_row = interface_down(interface0) + "\n"
                            link[2] = "down"
                        elif link_prev_status == "down":
                            new_row = "\n"
                    tc_mod_commands_file.write(new_row)

                for r in range(filler):
                    new_row = "\n"
                    tc_mod_commands_file.write(new_row)

                current_time += timestep_granularity

def get_node_pair_distance(CLUSTER_CONFIG, node0, node1, current_time):
    """Get the distance between node0 and node1, at the current time.

        Parameters:
            node0 (string)
            node1 (string)
            current_time (int): in seconds

        Output:
            distance (float): in meters
            or
            distance (string): "NAN"
    """
    current_time_ns = current_time * 1000 * 1000 * 1000
    LINK_DISTANCES_FILE = get_distance_file_for_node_timestep(CLUSTER_CONFIG, node0, current_time_ns)

    with open(LINK_DISTANCES_FILE, "r") as link_distances_file:
        for link_distance in link_distances_file:
            row = link_distance.split()
            assert len(row) == 2

            neig = row[0] # string variable
            if row[1] == "NAN":
                distance = "NAN"
            else:
                distance = float(row[1])

            if neig == node1:
                return distance

        raise ValueError("ValueError: could not find neigbour node from LINK_DISTANCES_FILE provided.")

def get_latency(distance):
    """Get latency given distance, and assuming speed of light.

        Parameters:
            distance (float): in meters

        Output:
            latency (int): in milliseconds (ms). Round up.

    """
    # Speed of light, since that is assumed in Hypatia as well
    # print(distance)
    SPEED_ms = 299792458.0
    latency = distance / SPEED_ms * 1000
    latency = int(round(latency))
    return latency

def delete_file_if_exists(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def get_distance_file_for_node_timestep(CLUSTER_CONFIG, node_string, time):
    """Get the node_string/link_distance_[timestep in ns].txt filename, associated with this cluster config.
    Note: this file contains all neighbours (and hence their distances from node_string) of node_string.

        Parameters:
            CLUSTER_CONFIG (dictionary)
            node_string (string): node name in string format
            time (integer): current time in nanoseconds

        Output: 
            output_filename (string)
    """
    constellation_name = CLUSTER_CONFIG["constellation_name"]
    main_gs = CLUSTER_CONFIG["main_gs"]
    timestep_granularity = int(CLUSTER_CONFIG["timestep_granularity"])
    simulation_time = int(CLUSTER_CONFIG["simulation_time"])

    timestep_granularity_ms = timestep_granularity * 1000

    mod_constellation_name = constellation_name.replace('-', '_').casefold()
    # mod_main_gs = main_gs.casefold()

    HYPATIA_PLUS_GEN_DIR = HYPATIA_PLUS_DIR + "/gen_data"
    INIT_ISL_TOPO = CLUSTER_CONFIG["init_isl_topo"]
    LINK_DISTANCES_DIR = "/{}_{}_ground_stations_top_100_algorithm_free_one_only_over_isls/dynamic_state_{}ms_for_{}s/{}".format(mod_constellation_name, INIT_ISL_TOPO, timestep_granularity_ms, simulation_time, node_string)

    LINK_DISTANCES_FILE = "/link_distances_{}.txt".format(time)

    return HYPATIA_PLUS_GEN_DIR + LINK_DISTANCES_DIR + LINK_DISTANCES_FILE

def count_actual_isls(links, node):
    """ Do not count sat-GS links.

        Parameters:
            links: a 2d list, in which each element of links represents a link, from "node" to links[i][0]
            node (string): the src node for which links[i][0] is the dst node 

        Output:
            (int): Actual number of ISLs for a given sat
    """
    count = 0
    if "g" in node:
        return 0
    else:
        for link in links:
            if "g" not in link[0]:
                count += 1
        return count

set_tc_mod_timer(CLUSTER_CONFIG)
set_tc_mod(CLUSTER_CONFIG)