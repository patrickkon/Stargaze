import sys
from config import *
sys.path.append(HYPATIA_DIR + "/satgenpy")
import satgen
import utils
import unittest
import os


class TestUtils(unittest.TestCase):

    output_generated_data_dir = "gen_test_data"

    def calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(self):
        
        isl_selection = "isls_plus_grid"

        # ISLs
        print("Generating ISLs...")
        if isl_selection == "isls_plus_grid":
            satgen.generate_plus_grid_isls(
                output_generated_data_dir + "/" + name + "/isls.txt",
                self.NUM_ORBS,
                self.NUM_SATS_PER_ORB,
                isl_shift=0,
                idx_offset=0
            )
        elif isl_selection == "isls_none":
            satgen.generate_empty_isls(
                output_generated_data_dir + "/" + name + "/isls.txt"
            )
        else:
            raise ValueError("Unknown ISL selection: " + isl_selection)

        # TLEs
        print("Generating TLEs...")
        satgen.generate_tles_from_scratch_manual(
            output_generated_data_dir + "/" + name + "/tles.txt",
            NICE_NAME,
            NUM_ORBS,
            NUM_SATS_PER_ORB,
            PHASE_DIFF,
            INCLINATION_DEGREE,
            ECCENTRICITY,
            ARG_OF_PERIGEE_DEGREE,
            MEAN_MOTION_REV_PER_DAY
        )

        tles = satgen.read_tles(output_generated_data_dir + "/" + name + "/tles.txt")
        satellites = tles["satellites"]
        list_isls = satgen.read_isls(output_generated_data_dir + "/" + name + "/isls.txt", len(satellites))
        epoch = tles["epoch"]
        # TODO fix imports and assertions..
        for (a, b) in list_isls:

            # ISLs are not permitted to exceed their maximum distance
            sat_distance_m = satgen.distance_m_between_satellites(satellites[a], satellites[b], str(epoch), str(time))
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
            if sat_distance_m != calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying(
                satellites[a],
                satellites[b],
                sat_net_graph_only_satellites_with_isls,
                enable_verbose_logs
            ):
                raise ValueError("calculate_fstate_shortest_path_for_selected_satellites_without_gs_relaying value incorrect.")

        with open("description.txt.tmp", "r") as f_in:
            i = 0
            for line in f_in:
                if i == 0:
                    self.assertEqual("max_gsl_length_m=19229.2424219420", line.strip())
                elif i == 1:
                    self.assertEqual("max_isl_length_m=1828282.2290193001", line.strip())
                else:
                    self.fail()
                i += 1
        os.remove("description.txt.tmp")
