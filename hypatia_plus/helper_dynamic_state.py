import sys
from config import HYPATIA_DIR
sys.path.append(HYPATIA_DIR + "/satgenpy")
from satgen.distance_tools import *
from satgen.isls import *
from satgen.ground_stations import *
from satgen.tles import *
from satgen.interfaces import *
import generate_dynamic_state
import os
import math
from multiprocessing.dummy import Pool as ThreadPool
from collections import defaultdict
import shutil

def node_string_to_int(CLUSTER_CONFIG, node):
    NUM_MASTERS = CLUSTER_CONFIG["num_masters"]
    NUM_WORKERS = CLUSTER_CONFIG["num_workers"]
    NUM_GS =CLUSTER_CONFIG["num_gs"]
    if "m" in node: # this is a master node:
        return int(node.split('m')[1])
    elif "g" in node:
        return int(node.split('g')[1]) + NUM_MASTERS + NUM_WORKERS
    elif "d" in node:
        return int(node.split('d')[1]) + NUM_MASTERS + NUM_WORKERS + NUM_GS
    else: # this is a worker node
        return int(node) + NUM_MASTERS

def worker(args):

    # Extract arguments
    (
        output_dynamic_state_dir,
        CLUSTER_CONFIG,
        CLUSTER_DIR,
        epoch,
        simulation_end_time_ns,
        time_step_ns,
        offset_ns,
        satellites,
        ground_stations,
        list_isls,
        list_gsl_interfaces_info,
        max_gsl_length_m,
        max_isl_length_m,
        dynamic_state_algorithm,
        node_to_sat_or_gs_mapping,
        print_logs
     ) = args

    # Generate dynamic state
    generate_dynamic_state.generate_dynamic_state(
        output_dynamic_state_dir,
        CLUSTER_CONFIG,
        CLUSTER_DIR,
        epoch,
        simulation_end_time_ns,
        time_step_ns,
        offset_ns,
        satellites,
        ground_stations,
        list_isls,
        list_gsl_interfaces_info,
        max_gsl_length_m,
        max_isl_length_m,
        dynamic_state_algorithm,  # Options:
                                  # "algorithm_free_one_only_gs_relays"
                                  # "algorithm_free_one_only_over_isls"
                                  # "algorithm_free_gs_one_sat_many_only_over_isls"
                                  # "algorithm_paired_many_only_over_isls"
        node_to_sat_or_gs_mapping,
        print_logs
    )


def help_dynamic_state(
        output_generated_data_dir, CLUSTER_CONFIG, CLUSTER_DIR, num_threads, name, time_step_ms, duration_s,
        max_gsl_length_m, max_isl_length_m, dynamic_state_algorithm, print_logs
):

    # Directory
    output_dynamic_state_dir = output_generated_data_dir + "/" + name + "/dynamic_state_" + str(time_step_ms) \
                               + "ms_for_" + str(duration_s) + "s"
    if not os.path.isdir(output_dynamic_state_dir):
        os.makedirs(output_dynamic_state_dir)

    # In nanoseconds
    simulation_end_time_ns = duration_s * 1000 * 1000 * 1000
    time_step_ns = time_step_ms * 1000 * 1000

    num_calculations = math.floor(simulation_end_time_ns / time_step_ns)
    calculations_per_thread = int(math.floor(float(num_calculations) / float(num_threads)))
    num_threads_with_one_more = num_calculations % num_threads

    # Variables (load in for each thread such that they don't interfere)
    # NOTE: therefore, all the prerequisite files (Except for dynamic_state/ dir) mentioned in https://github.com/patrickkon/hypatia/tree/master/satgenpy,
    # are used to generate dynamic_state/ dir
    ground_stations = read_ground_stations_extended(output_generated_data_dir + "/" + name + "/ground_stations.txt")
    tles = read_tles(output_generated_data_dir + "/" + name + "/tles.txt")
    satellites = tles["satellites"]
    list_isls = read_isls(output_generated_data_dir + "/" + name + "/isls.txt", len(satellites))
    # This just converts the file into a list (with the exception of the first column which represents ID. This is now implicitly attached to the order)
    list_gsl_interfaces_info = read_gsl_interfaces_info(
        output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
        len(satellites),
        len(ground_stations)
    )
    epoch = tles["epoch"]

    # SECTION: Create mapping for nodes defined in topo.txt and satellites
    node_to_sat_or_gs_mapping_file_exists = CLUSTER_CONFIG["node_to_sat_or_gs_mapping_file"] 
    main_gs = CLUSTER_CONFIG["main_gs"]
    main_node = CLUSTER_CONFIG["main_node"]
    NUM_MASTERS = int(CLUSTER_CONFIG["num_masters"])
    main_node_adjusted = node_string_to_int(CLUSTER_CONFIG, main_node)

    # Create required directories:
    TOPO_FILE = CLUSTER_DIR + "/" + CLUSTER_CONFIG["topo_file"]
    with open(TOPO_FILE, "r") as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 2
            a = row[0]
            b = row[1]

            output_dynamic_state_dir_node_dir = output_dynamic_state_dir + "/" + a
            if os.path.exists(output_dynamic_state_dir_node_dir):
                # delete directory if it already exists
                shutil.rmtree(output_dynamic_state_dir_node_dir)
            os.makedirs(output_dynamic_state_dir_node_dir, exist_ok=True)

            output_dynamic_state_dir_node_dir = output_dynamic_state_dir + "/" + b
            if os.path.exists(output_dynamic_state_dir_node_dir):
                # delete directory if it already exists
                shutil.rmtree(output_dynamic_state_dir_node_dir)
            os.makedirs(output_dynamic_state_dir_node_dir, exist_ok=True)
            
    node_to_sat_or_gs_mapping = defaultdict(int) # note node (i.e. key) is also in pure integer, e.g. not like m0 but 0
    NODE_TO_SAT_OR_GS_MAPPING_FILE = output_generated_data_dir + "/" + name + "/node_to_sat_or_gs_mapping.txt" # this is the final output file for the mapping
    # Note: we can be sure list_isls will only contain isls in topo.txt, as this was performed in main_helper.py
    # Format: {node0: [node1]}. We use this to store links, in this example, node0-node1 is a link
    graph = defaultdict(list)
    for (a, b) in list_isls:
        graph[a].append(b)
        graph[b].append(a)
    num_vertices = len(graph.keys())
    if not node_to_sat_or_gs_mapping_file_exists: # we perform auto node_to_sat_or_gs_mapping only if a mapping file was not already provided by the user
        # Note: Currently, we are only hardcoding a few main_gs, e.g. "Paris"
        for gs in ground_stations:
            if gs["name"] == main_gs:
                main_gs = gs

        # Assign main_node to the closest possible satellite to main_gs, at time 0 (i.e. epoch + 0)
        # NOTE: this is actually affected by angle of elevation. They use distance as a proxy. MAX_GSL_LENGTH_M is affected by SATELLITE_CONE_RADIUS_M and ALTITUDE_M
        satellites_in_range = []
        time = epoch
        for sid in range(len(satellites)):
            distance_m = distance_m_ground_station_to_satellite(
                main_gs,
                satellites[sid],
                str(epoch),
                str(time),
            )
            if sid == 1522 or sid == 1523 or sid ==1524:
                print("sat {}: {}".format(sid, distance_m))
            if distance_m <= max_gsl_length_m:
                satellites_in_range.append((distance_m, sid))
        satellites_in_range.sort(key=lambda x: x[0])
        assert len(satellites) >= 2 and satellites_in_range[0][0] <= satellites_in_range[1][0] # make sure the sort worked

        main_sat_sid = satellites_in_range[0][1] # here we have completed the first mapping, which was for main_node
        main_sat = satellites[main_sat_sid]
        node_to_sat_or_gs_mapping[main_node_adjusted] = main_sat_sid

        # Complete the mapping for all other nodes.
        visited_nodes = [False]*num_vertices
        selected_satellite_sids = [False]*len(satellites)
        queued_nodes = []

        queued_nodes.append(main_node_adjusted)
        visited_nodes[main_node_adjusted] = True
        selected_satellite_sids[main_sat_sid] = True
        # Perform a bfs on our graph (containing our nodes and ISLs), to iteratively pair up all nodes with satellites
        while False in visited_nodes:
            try:
                s = queued_nodes.pop(0)
            except IndexError:
                raise IndexError("topo.txt provided a topology that is a non-connected graph. Please ensure the graph is connected.")
            visited_nodes[s] = True
            for i in graph[s]:
                if visited_nodes[i] == False:
                    queued_nodes.append(i)

                    # Subsection: Current policy is we traverse each neighbour of current node in sequence, and assign the closest possible satellite (to the satellite assigned to current node). This is not necessarily the best/simplest approach

                    # Try and map with satellites in range of main_gs first if possible:
                    min_dist_sat_sid = -1
                    min_dist = math.inf
                    for sat_det in satellites_in_range:
                        if selected_satellite_sids[sat_det[1]] == False: # the current sat (i.e. sat_det) has not been mapped to a node yet
                            sat_distance_m = distance_m_between_satellites(satellites[node_to_sat_or_gs_mapping[s]], satellites[sat_det[1]], str(epoch), str(time))
                            # ISLs are not permitted to exceed their maximum distance
                            # TODO: Technically, they can (could just be ignored by forwarding state calculation),
                            # TODO: but practically, defining a permanent ISL between two satellites which
                            # TODO: can go out of distance is generally unwanted
                            if sat_distance_m > max_isl_length_m:
                                if 0:
                                    print(
                                        "Warning: Skipped.The distance between two satellites (%d and %d) "
                                        "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                                        % (node_to_sat_or_gs_mapping[s], sat_det[1], sat_distance_m, max_isl_length_m, 0)
                                    )
                                continue
                            if min_dist > sat_distance_m:
                                min_dist = sat_distance_m
                                min_dist_sat_sid = sat_det[1]

                    if min_dist_sat_sid == -1: # this only happens if there are no satellites_in_range that can be linked (to s) because they are already all occupied
                        # check through all satellites in the constellation, to find the unoccupied satellite that has the shortest distance to satellite assigned to currnet node.
                        for sid in range(len(satellites)):
                            if selected_satellite_sids[sid] == False: # the current sat (i.e. sat_det) has not been mapped to a node yet
                                sat_distance_m = distance_m_between_satellites(satellites[node_to_sat_or_gs_mapping[s]], satellites[sid], str(epoch), str(time))
                                # ISLs are not permitted to exceed their maximum distance
                                # TODO: Technically, they can (could just be ignored by forwarding state calculation),
                                # TODO: but practically, defining a permanent ISL between two satellites which
                                # TODO: can go out of distance is generally unwanted
                                if sat_distance_m > max_isl_length_m:
                                    if 0:
                                        print(
                                            "Warning: Skipped. The distance between two satellites (%d and %d) "
                                            "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                                            % (node_to_sat_or_gs_mapping[s], sid, sat_distance_m, max_isl_length_m, 0)
                                        )
                                    continue
                                if min_dist > sat_distance_m:
                                    min_dist = sat_distance_m
                                    min_dist_sat_sid = sid
                    print("Found satellite pairing for node {}: satellite sid {}. Distance: {}".format(i, min_dist_sat_sid, min_dist))
                    selected_satellite_sids[min_dist_sat_sid] = True
                    node_to_sat_or_gs_mapping[i] = min_dist_sat_sid
    else:
        PROVIDED_NODE_TO_SAT_OR_GS_MAPPING_FILE = CLUSTER_DIR + "/" + CLUSTER_CONFIG["node_to_sat_or_gs_mapping_file"]
        with open(PROVIDED_NODE_TO_SAT_OR_GS_MAPPING_FILE, 'r') as provided_mapping_file:
            for mapping in provided_mapping_file:
                row = mapping.split()
                assert len(row) == 2
                node = node_string_to_int(CLUSTER_CONFIG, row[0])
                node_to_sat_or_gs_mapping[node] = int(row[1])

    # Check that the node to sat mapping was successful:
    # assert len(node_to_sat_or_gs_mapping.keys()) == num_vertices + 2
    assert -1 not in node_to_sat_or_gs_mapping.values()

    # output_dynamic_state_dir + "/sats_in_range_of_GS" + str(time_since_epoch_ns) + ".txt"
    with open(NODE_TO_SAT_OR_GS_MAPPING_FILE, "w") as node_to_sat_or_gs_mapping_file:
        for k, v in node_to_sat_or_gs_mapping.items():
            node_to_sat_or_gs_mapping_file.write("{} {}\n".format(k, v))

    # Prepare arguments
    current = 0
    list_args = []
    for i in range(num_threads):

        # How many time steps to calculate for
        num_time_steps = calculations_per_thread
        if i < num_threads_with_one_more:
            num_time_steps += 1

        # Print goal
        print("Thread %d does interval [%.2f ms, %.2f ms]" % (
            i,
            (current * time_step_ns) / 1e6,
            ((current + num_time_steps) * time_step_ns) / 1e6
        ))

        # NOTE: this means, we loop through threads (above) sequentially, and each such thread processes a given number of time steps, roughly like so:
        # [current_time_step, current_time_step + num_of_time_steps]. Thus, for example, in a scenario with 2 threads and 20 time steps:
        # first thread: [0, 10], second thread: [11, 20]
        list_args.append((
            output_dynamic_state_dir,
            CLUSTER_CONFIG,
            CLUSTER_DIR,
            epoch, # Refers to start time. in our example above, this would be 0
            (current + num_time_steps) * time_step_ns + time_step_ns, # simulation_end_time_ns. Refers to "current_time_step + num_of_time_steps"
            time_step_ns,
            current * time_step_ns, # offset_ns. This refers to the starting time step time: i.e. "current_time_step"
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            dynamic_state_algorithm,
            node_to_sat_or_gs_mapping,
            print_logs
        ))

        current += num_time_steps

    # Run in parallel
    pool = ThreadPool(num_threads)
    pool.map(worker, list_args)
    pool.close()
    pool.join()
