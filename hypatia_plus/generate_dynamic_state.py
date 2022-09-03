import sys
from config import HYPATIA_DIR
sys.path.append(HYPATIA_DIR + "/satgenpy")
from satgen.distance_tools import *
from astropy import units as u
import math
import networkx as nx
import numpy as np
from satgen.dynamic_state.algorithm_free_one_only_gs_relays import algorithm_free_one_only_gs_relays
from satgen.dynamic_state.algorithm_free_one_only_over_isls import algorithm_free_one_only_over_isls
from satgen.dynamic_state.algorithm_paired_many_only_over_isls import algorithm_paired_many_only_over_isls
from satgen.dynamic_state.algorithm_free_gs_one_sat_many_only_over_isls import algorithm_free_gs_one_sat_many_only_over_isls
import utils


def generate_dynamic_state(
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
                                  # "algorithm_paired_many_only_over_isls"
        node_to_sat_or_gs_mapping,
        enable_verbose_logs
):
    if offset_ns % time_step_ns != 0:
        raise ValueError("Offset must be a multiple of time_step_ns")
    prev_output = None
    i = 0
    total_iterations = ((simulation_end_time_ns - offset_ns) / time_step_ns)
    for time_since_epoch_ns in range(offset_ns, simulation_end_time_ns, time_step_ns):
        if not enable_verbose_logs:
            if i % int(math.floor(total_iterations) / 10.0) == 0:
                print("Progress: calculating for T=%d (time step granularity is still %d ms)" % (
                    time_since_epoch_ns, time_step_ns / 1000000
                ))
            i += 1
        prev_output = generate_dynamic_state_at(
            output_dynamic_state_dir,
            CLUSTER_CONFIG,
            CLUSTER_DIR,
            epoch,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            dynamic_state_algorithm,
            node_to_sat_or_gs_mapping,
            prev_output,
            enable_verbose_logs
        )


def generate_dynamic_state_at(
        output_dynamic_state_dir,
        CLUSTER_CONFIG,
        CLUSTER_DIR,
        epoch,
        time_since_epoch_ns,
        satellites,
        ground_stations,
        list_isls,
        list_gsl_interfaces_info,
        max_gsl_length_m,
        max_isl_length_m,
        dynamic_state_algorithm,
        node_to_sat_or_gs_mapping,
        prev_output,
        enable_verbose_logs
):
    if enable_verbose_logs:
        print("FORWARDING STATE AT T = " + (str(time_since_epoch_ns))
              + "ns (= " + str(time_since_epoch_ns / 1e9) + " seconds)")

    #################################

    if enable_verbose_logs:
        print("\nBASIC INFORMATION")

    # Time
    time = epoch + time_since_epoch_ns * u.ns
    if enable_verbose_logs:
        print("  > Epoch.................. " + str(epoch)) # note again that epoch refers to absolute start time, defined in "help_dynamic_state" function. 
        print("  > Time since epoch....... " + str(time_since_epoch_ns) + " ns")
        print("  > Absolute time.......... " + str(time))

    # Graphs
    sat_net_graph_only_satellites_with_isls = nx.Graph() # contains nodes (that represent satellites) and edges (that represent distance)
    sat_net_graph_all_with_only_gsls = nx.Graph() # contains nodes (that represent satellites + GS) and edges (that represent distance)

    # Information
    for i in range(len(satellites)):
        sat_net_graph_only_satellites_with_isls.add_node(i)
        sat_net_graph_all_with_only_gsls.add_node(i)
    for i in range(len(satellites) + len(ground_stations)):
        sat_net_graph_all_with_only_gsls.add_node(i)
    if enable_verbose_logs:
        print("  > Satellites............. " + str(len(satellites)))
        print("  > Ground stations........ " + str(len(ground_stations)))
        print("  > Max. range GSL......... " + str(max_gsl_length_m) + "m")
        print("  > Max. range ISL......... " + str(max_isl_length_m) + "m")

    #################################

    if enable_verbose_logs:
        print("\nISL INFORMATION")

    # ISL edges
    total_num_isls = 0
    num_isls_per_sat = [0] * len(satellites)
    sat_neighbor_to_if = {}

    utils.write_distances_for_timestep_for_nodes(output_dynamic_state_dir, CLUSTER_CONFIG, CLUSTER_DIR, satellites, ground_stations, node_to_sat_or_gs_mapping, time_since_epoch_ns, epoch, time, max_isl_length_m, max_gsl_length_m)

    return # currently just return since we do not need what's provided next, and because it results in an error (possibly a and b will have ISL length exceeded) because we have not corrected list_isls to refer to satellites instead of our compute nodes.

    for (a, b) in list_isls:

        # ISLs are not permitted to exceed their maximum distance
        # TODO: Technically, they can (could just be ignored by forwarding state calculation),
        # TODO: but practically, defining a permanent ISL between two satellites which
        # TODO: can go out of distance is generally unwanted
        # print("sat {}: sat{}".format(a, b))
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

        # Verify the above:
        # if sat_distance_m != utils.calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(
        #     a,
        #     b,
        #     sat_net_graph_only_satellites_with_isls,
        #     enable_verbose_logs
        # ):
        #     raise ValueError("calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying value incorrect.")

        # Interface mapping of ISLs
        # This is the interface number/ID for each satellite's ISL interface. If a satellite has 4 ISLs connected to other satellites, it's interfaces will be uniquely
        # numbered from [0, 3]. This is why as shown in the next 2 rows, both ends of an ISL connection may have different interface ID: 
        # e.g. for sat a this could be interface 0, but for sat b this could be interface 1. 
        sat_neighbor_to_if[(a, b)] = num_isls_per_sat[a]
        sat_neighbor_to_if[(b, a)] = num_isls_per_sat[b]
        num_isls_per_sat[a] += 1
        num_isls_per_sat[b] += 1
        total_num_isls += 1 # for what? Probably remove this

    if enable_verbose_logs:
        print("  > Total ISLs............. " + str(len(list_isls)))
        print("  > Min. ISLs/satellite.... " + str(np.min(num_isls_per_sat)))
        print("  > Max. ISLs/satellite.... " + str(np.max(num_isls_per_sat)))

    #################################

    if enable_verbose_logs:
        print("\nGSL INTERFACE INFORMATION")

    satellite_gsl_if_count_list = list(map(
        lambda x: x["number_of_interfaces"],
        list_gsl_interfaces_info[0:len(satellites)]
    ))
    ground_station_gsl_if_count_list = list(map(
        lambda x: x["number_of_interfaces"],
        list_gsl_interfaces_info[len(satellites):(len(satellites) + len(ground_stations))]
    ))
    if enable_verbose_logs:
        print("  > Min. GSL IFs/satellite........ " + str(np.min(satellite_gsl_if_count_list)))
        print("  > Max. GSL IFs/satellite........ " + str(np.max(satellite_gsl_if_count_list)))
        print("  > Min. GSL IFs/ground station... " + str(np.min(ground_station_gsl_if_count_list)))
        print("  > Max. GSL IFs/ground_station... " + str(np.max(ground_station_gsl_if_count_list)))

    #################################

    if enable_verbose_logs:
        print("\nGSL IN-RANGE INFORMATION")

    # What satellites can a ground station see
    # NOTE: this is actually affected by angle of elevation. They use distance as a proxy. MAX_GSL_LENGTH_M is affected by SATELLITE_CONE_RADIUS_M and ALTITUDE_M
    ground_station_satellites_in_range = []
    for ground_station in ground_stations:
        # Find satellites in range
        satellites_in_range = []
        for sid in range(len(satellites)):
            distance_m = distance_m_ground_station_to_satellite(
                ground_station,
                satellites[sid],
                str(epoch),
                str(time)
            )
            if distance_m <= max_gsl_length_m:
                satellites_in_range.append((distance_m, sid))
                sat_net_graph_all_with_only_gsls.add_edge(
                    sid, len(satellites) + ground_station["gid"], weight=distance_m
                )

        ground_station_satellites_in_range.append(satellites_in_range)

    # Print how many are in range
    ground_station_num_in_range = list(map(lambda x: len(x), ground_station_satellites_in_range))
    if enable_verbose_logs:
        print("  > Min. satellites in range... " + str(np.min(ground_station_num_in_range)))
        print("  > Max. satellites in range... " + str(np.max(ground_station_num_in_range)))

    # selected_satellites = 

    utils.write_sats_in_range_of_GS_at_time_step(output_dynamic_state_dir, time_since_epoch_ns, ground_station_satellites_in_range, enable_verbose_logs)
    # utils.calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(
    #     output_dynamic_state_dir,
    #     time_since_epoch_ns,
    #     satellites,
    #     selected_satellites,
    #     ground_stations,
    #     sat_net_graph_only_satellites_with_isls,
    #     num_isls_per_sat,
    #     ground_station_satellites_in_range,
    #     sat_neighbor_to_if,
    #     enable_verbose_logs
    # )

    #################################

    #
    # Call the dynamic state algorithm which:
    #
    # (a) Output the gsl_if_bandwidth_<t>.txt files
    # (b) Output the fstate_<t>.txt files
    #
    # NOTE: better explanation. ALL these dynamic state algorithms are there to compute (and return) the "best next hop" for each satellite (and by extension, each GS) to each GS,
    # in the current time step (i.e. "time_since_epoch_ns"). Refer to notes in "calculate_fstate_shortest_path_without_gs_relaying" function for details. 
    # THIS IS WHAT dynamic state means. 
    if dynamic_state_algorithm == "algorithm_free_one_only_over_isls":

        return algorithm_free_one_only_over_isls(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )

    elif dynamic_state_algorithm == "algorithm_free_gs_one_sat_many_only_over_isls":

        return algorithm_free_gs_one_sat_many_only_over_isls(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )

    elif dynamic_state_algorithm == "algorithm_free_one_only_gs_relays":

        return algorithm_free_one_only_gs_relays(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_all_with_only_gsls,
            num_isls_per_sat,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )

    elif dynamic_state_algorithm == "algorithm_paired_many_only_over_isls":

        return algorithm_paired_many_only_over_isls(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )

    else:
        raise ValueError("Unknown dynamic state algorithm: " + str(dynamic_state_algorithm))
