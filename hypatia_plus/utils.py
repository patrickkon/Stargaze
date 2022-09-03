import math
import networkx as nx
from astropy import units as u
import sys
from config import HYPATIA_DIR
sys.path.append(HYPATIA_DIR + "/satgenpy")
from satgen.distance_tools import distance_m_between_satellites, distance_m_ground_station_to_satellite
from collections import defaultdict


# Obtain satellite and GS position info. # perhaps scrap this
def temp():
    return 

def write_sats_in_range_of_GS_at_time_step(output_dynamic_state_dir, time_since_epoch_ns, ground_station_satellites_in_range, enable_verbose_logs):
    """Get satellites in range of each GS at this time step.
    
    Output file format for each row: <ground_station_id> <distance from sat a to this ground station> <sat a id> .... 
    """
    # input_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    # if enable_verbose_logs:
    #     print("  > Getting list of satellites in range of a GS from: " + input_filename)
    # with open(input_filename, "r") as f_in:
    #     for line in f_in:
    #         path_str = line.split(",")
    #         if path_str[1] == path_str[2]:
    # NOTE: in the current implementation, previous calls that have the same time_since_epoch_ns will be OVERWRITTEN
    output_filename = output_dynamic_state_dir + "/sats_in_range_of_GS" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing list of satellites in range of a GS to: " + output_filename)
    with open(output_filename, "w+") as f_out:
        for gs_id in range(len(ground_station_satellites_in_range)):
            sat_string = ""
            for sats in ground_station_satellites_in_range[gs_id]:
                sat_string += " " + str(sats[0]) + " " + str(sats[1])
            f_out.write("%s,%s\n" % (
                gs_id,
                sat_string
            ))
 
def get_isls(output_generated_data_dir, satellites):
    """Get all ISLs (+grid and intra orbital plane) in the constellation. 
    
    Note: we expect ISLs to remain permanent. That is, we assume traditional +grid for now, despite its shortcomings. 
    Note: this does not verify that ISLs are connected (i.e. are within max length of ISLs for the given constellation's altitude). 
            For that, refer to "get_verified_isls_at_time_step" below.
    """
    
    list_isls = read_isls(output_generated_data_dir + "/" + name + "/isls.txt", len(satellites))

    return list_isls

def get_verified_isls_at_time_step(satellites, list_isls, epoch, time_since_epoch_ns, max_isl_length_m):
    """Get a network containing satellites and ISLs (+grid and intra orbital plane) 
    in range (note we do not expect this to change much) of a given group of satellites, at this time step.
    
    Note: this function is trivial, derived from generate_dynamic_state.py
    """
    time = epoch + time_since_epoch_ns * u.ns
    sat_net_graph_only_satellites_with_isls = nx.Graph() # contains nodes (that represent satellites) and edges (that represent distance)

    for (a, b) in list_isls:

        # ISLs are not permitted to exceed their maximum distance
        # TODO: Technically, they can (could just be ignored by forwarding state calculation),
        # TODO: but practically, defining a permanent ISL between two satellites which
        # TODO: can go out of distance is generally unwanted
        sat_distance_m = distance_m_between_satellites(satellites[a], satellites[b], str(epoch), str(time))
        if sat_distance_m > max_isl_length_m:
            raise ValueError(
                "The distance between two satellites (%d and %d) "
                "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                % (a, b, sat_distance_m, max_isl_length_m, time_since_epoch_ns)
            )

        # Add to networkx graph
        sat_net_graph_only_satellites_with_isls.add_edge(
            a, b, weight=sat_distance_m
        )
    
    return sat_net_graph_only_satellites_with_isls

def calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(
        src_sat_id,
        dst_sat_id,
        sat_net_graph_only_satellites_with_isls_at_selected_time_step,
        enable_verbose_logs
):
    """Get shortest path (if does not exist, return math.inf), for selected src and dst satellite, 
    utilizing "get_verified_isls_at_time_step".

    Output:
        Distance metric if path exists, 
        inf if path does not exist
    """

    # Calculate shortest path distances
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for src sat %d and dst sat %d, using graph without ground-station relays: " %(src_sat_id, dst_sat_id))
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls_at_selected_time_step)

    distance = dist_sat_net_without_gs[(src_sat_id, dst_sat_id)]
    if not math.isinf(distance):
        return distance
    else:
        return math.inf

def write_distances_for_timestep_for_nodes(output_dynamic_state_dir, CLUSTER_CONFIG, CLUSTER_DIR, satellites, ground_stations, node_to_sat_or_gs_mapping, time_since_epoch_ns, epoch, time, max_isl_length_m, max_gsl_length_m):
    """Write distances to all neighbours of each node (in a distinct directory) for the current timestep (as a distinct file). Includes ISLs and GS-sat link distances. 

        File output (side-effect):
            if gs to sat distance <= max_gsl_length_m: write distance
            else write 'NAN'
            if ISL distance <= max_isl_length_m: write distance
            else throw error

        Note: for a gs-sat link, we consider gs and that sat to be neighbours too
        Note: currently, we throw an error if ISL link distance exceeds max_isl_length_m, but this does not preclude future enhancements to model link unavailability
        Note: currently we only have 2 gses: main and destination gs, but this does not preclude enhancements to have more gses that we can send or receive info along the way.
        Note: does not include GS-GS link distances. We assume this cannot exist for now.
    """
    # sat_to_node_mapping = {v: k for k, v in node_to_sat_or_gs_mapping.items()}
    UNAVAILABLE_KEYWORD = 'NAN'

    def node_int_to_string(node):
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

    def node_string_to_int(node):
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

    def gs_string_to_gs(gs_string):
        for gs in ground_stations:
            if gs["name"] == gs_string:
                return gs
    
    def gs_int_to_gs(gs_int):
        for gs in ground_stations:
            if gs["gid"] == gs_int:
                return gs

    def distance_satgs_abstracted(gs, sat_id):
        # print (gs)
        distance_m = distance_m_ground_station_to_satellite(
                gs,
                satellites[sat_id],
                str(epoch),
                str(time)
        )
        if distance_m <= max_gsl_length_m:
            return distance_m
        else:
            return UNAVAILABLE_KEYWORD

    # Create graph to get all neighbours of each node
    TOPO_FILE = CLUSTER_DIR + "/" + CLUSTER_CONFIG["topo_file"]
    # Format: {node0: [node1]}. We use this to store links, in this example, node0-node1 is a link
    graph = defaultdict(list) 
    with open(TOPO_FILE, "r") as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 2
            a = row[0]
            b = row[1]
            a = node_string_to_int(a)
            b = node_string_to_int(b)
            graph[a].append(b)
            graph[b].append(a)
    # num_vertices = len(graph.keys())

    main_gs = gs_string_to_gs(CLUSTER_CONFIG['main_gs'])
    no_dest_gs = False
    if CLUSTER_CONFIG['destination_gs']:
        destination_gs = gs_string_to_gs(CLUSTER_CONFIG['destination_gs'])
    else:
        no_dest_gs = True

    # Write distances for node to all its neighbours for the current timestep
    for node, neighbours in graph.items():
        node_string = node_int_to_string(node)

        output_dynamic_state_dir_node_dir = output_dynamic_state_dir + "/" + node_string
        NODE_TO_NEIGBHOUR_DISTANCES_FILE = output_dynamic_state_dir_node_dir + "/link_distances_" + str(time_since_epoch_ns) + ".txt"

        with open(NODE_TO_NEIGBHOUR_DISTANCES_FILE, "w") as node_to_neighbour_distances_file:
            sat_a = node_to_sat_or_gs_mapping[node]
            for neig in neighbours:
                sat_b = node_to_sat_or_gs_mapping[neig]

                sat_a_string = node_int_to_string(node)
                sat_b_string = node_int_to_string(neig)
                
                if "g" in sat_a_string: # sat_a is actually a gs. Note we assume that GS-GS links do not exist
                    gs = gs_int_to_gs(sat_a - len(satellites))
                    if not no_dest_gs:
                        assert gs["name"] == main_gs["name"] or gs["name"] == destination_gs["name"] # ensure we are actually getting intended gs, as named in cluster_config.yaml
                    else:
                        assert gs["name"] == main_gs["name"]
                    distance = distance_satgs_abstracted(gs, sat_b)
                    node_to_neighbour_distances_file.write("{} {}\n".format(sat_b_string, distance))
                elif "g" in sat_b_string: # sat_b is actually a gs. Note we assume that GS-GS links do not exist
                    gs = gs_int_to_gs(sat_b - len(satellites))
                    # print(gs["name"] , main_gs["name"] , gs["name"] , destination_gs["name"])
                    if not no_dest_gs:
                        assert gs["name"] == main_gs["name"] or gs["name"] == destination_gs["name"] # ensure we are actually getting intended gs, as named in cluster_config.yaml
                    else:
                        assert gs["name"] == main_gs["name"]
                    distance = distance_satgs_abstracted(gs, sat_a)
                    node_to_neighbour_distances_file.write("{} {}\n".format(sat_b_string, distance))
                else:
                    sat_distance_m = distance_m_between_satellites(satellites[sat_a], satellites[sat_b], str(epoch), str(time))
                    if sat_distance_m > max_isl_length_m:
                        raise ValueError(
                            "The distance between two satellites (%d and %d) "
                            "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                            % (sat_a, sat_b, sat_distance_m, max_isl_length_m, time_since_epoch_ns)
                        )
                    # Format: each row: neighbour node in string format, distance in m to node (i.e. the node specified as the parent folder name)
                    node_to_neighbour_distances_file.write("{} {}\n".format(node_int_to_string(neig), sat_distance_m))

# Note: with some corrections, this can be used for writing a file similar to the /fstate_ files, for routing or visualization purposes. 
# def calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(
#         output_dynamic_state_dir,
#         time_since_epoch_ns,
#         satellites, # all satellites in the constellation
#         selected_satellites, # satellites that the user selected for all pairs shortest path. 
#         ground_stations,
#         sat_net_graph_only_satellites_with_isls,
#         num_isls_per_sat,
#         ground_station_satellites_in_range_candidates,
#         sat_neighbor_to_if,
#         enable_verbose_logs
# ):
#     """Get all pairs shortest paths, for all satellites of choice (selected_satellites), 
#     utilizing "get_verified_isls_at_time_step".

#     Output:
#       Almost the same as the /fstate_ files, possibly with the addition of a "distance" column at the end of each row. 
#     """
#     num_satellites = len(satellites)
#     num_ground_stations = len(ground_stations)
#     gid_to_sat_gsl_if_idx = list(range(len(ground_stations)))

#     # Calculate shortest path distances
#     if enable_verbose_logs:
#         print("  > Calculating all pairs Floyd-Warshall for graph without ground-station relays")
#     # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
#     dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)

#     # Forwarding state
#     fstate = {}

#     # Now write state to file for complete graph
#     output_filename = output_dynamic_state_dir + "/sat_fstate_" + str(time_since_epoch_ns) + ".txt"
#     if enable_verbose_logs:
#         print("  > Writing forwarding state to: " + output_filename)
#     with open(output_filename, "w+") as f_out:

#         # Satellites to satellites
#         # From the satellites attached to the destination ground station,
#         # select the one which promises the shortest path to the destination ground station (getting there + last hop)
#         # NOTE: alternative explanation: for each satellite, find the neighbour (which could be the destination itself, i.e. the GS) which will give the shortest path,
#         # to reach each GS (the destination). i.e. find the best next hop
#         dist_satellite_to_ground_station = {}
#         for curr in range(num_satellites):
#             for dst_gid in range(num_ground_stations):
#                 dst_gs_node_id = num_satellites + dst_gid

#                 # Among the satellites in range of the destination ground station,
#                 # find the one which promises the shortest distance
#                 possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
#                 possibilities = []
#                 for b in possible_dst_sats:
#                     if not math.isinf(dist_sat_net_without_gs[(curr, b[1])]):  # Must be reachable
#                         possibilities.append(
#                             (
#                                 dist_sat_net_without_gs[(curr, b[1])] + b[0],
#                                 b[1]
#                             )
#                         )
#                 possibilities = list(sorted(possibilities))

#                 # By default, if there is no satellite in range for the
#                 # destination ground station, it will be dropped (indicated by -1)
#                 next_hop_decision = (-1, -1, -1) # neighbour_id, interface ID of curr (that is connected to neighbour), interface ID of neighbour (that is connected to curr)
#                 distance_to_ground_station_m = float("inf")
#                 if len(possibilities) > 0:
#                     dst_sat = possibilities[0][1]
#                     distance_to_ground_station_m = possibilities[0][0]

#                     # If the current node is not that satellite, determine how to get to the satellite
#                     if curr != dst_sat:

#                         # Among its neighbors, find the one which promises the
#                         # lowest distance to reach the destination satellite
#                         best_distance_m = 1000000000000000
#                         for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
#                             distance_m = (
#                                     sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
#                                     +
#                                     dist_sat_net_without_gs[(neighbor_id, dst_sat)]
#                             )
#                             if distance_m < best_distance_m:
#                                 next_hop_decision = (
#                                     neighbor_id,
#                                     sat_neighbor_to_if[(curr, neighbor_id)],
#                                     sat_neighbor_to_if[(neighbor_id, curr)]
#                                 )
#                                 best_distance_m = distance_m

#                     else:
#                         # This is the destination satellite, as such the next hop is the ground station itself
#                         next_hop_decision = (
#                             dst_gs_node_id,
#                             num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
#                             0
#                         )

#                 # In any case, save the distance of the satellite to the ground station to re-use
#                 # when we calculate ground station to ground station forwarding
#                 dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = distance_to_ground_station_m

#                 # Write to forwarding state
#                 # NOTE: alternative explanation: only write best next hop to fstate files, IFF there are changes to the best next hop for each satellite. 
#                 # e.g. if satellite 0 best next hop to GS 1 in previous time step (i.e. prev "time_since_epoch_ns") was satellite 1, and it is still satellite 1 in current
#                 # time step, we do not update (i.e. we do not write to fstate files). THIS IS THE REASON the subsequent fstate_*.txt files can be empty. 
#                 if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
#                     f_out.write("%d,%d,%d,%d,%d\n" % (
#                         curr,
#                         dst_gs_node_id,
#                         next_hop_decision[0],
#                         next_hop_decision[1],
#                         next_hop_decision[2]
#                     ))
#                 fstate[(curr, dst_gs_node_id)] = next_hop_decision

#         # Ground stations to ground stations
#         # Choose the source satellite which promises the shortest path
#         for src_gid in range(num_ground_stations):
#             for dst_gid in range(num_ground_stations):
#                 if src_gid != dst_gid:
#                     src_gs_node_id = num_satellites + src_gid
#                     dst_gs_node_id = num_satellites + dst_gid

#                     # Among the satellites in range of the source ground station,
#                     # find the one which promises the shortest distance
#                     possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
#                     possibilities = []
#                     for a in possible_src_sats:
#                         best_distance_offered_m = dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]
#                         if not math.isinf(best_distance_offered_m):
#                             possibilities.append(
#                                 (
#                                     a[0] + best_distance_offered_m,
#                                     a[1]
#                                 )
#                             )
#                     possibilities = sorted(possibilities)

#                     # By default, if there is no satellite in range for one of the
#                     # ground stations, it will be dropped (indicated by -1)
#                     next_hop_decision = (-1, -1, -1)
#                     if len(possibilities) > 0:
#                         src_sat_id = possibilities[0][1]
#                         next_hop_decision = (
#                             src_sat_id,
#                             0,
#                             num_isls_per_sat[src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
#                         )

#                     # Update forwarding state
#                     if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
#                         f_out.write("%d,%d,%d,%d,%d\n" % (
#                             src_gs_node_id,
#                             dst_gs_node_id,
#                             next_hop_decision[0],
#                             next_hop_decision[1],
#                             next_hop_decision[2]
#                         ))
#                     fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision

#     # Finally return result
#     return fstate



# Get link utilization (ISLs and GS-sat link) at this time step.
def temp2():
    return

# Notify k8s cluster scheduler at every time step. # may move this to extractor.py insted. 