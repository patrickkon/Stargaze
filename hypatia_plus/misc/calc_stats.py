import glob
from collections import Counter

# Note the number of iterations is determined by the number of time steps required to reach from start (epoch) to end time. 

# Init as many counters as there are GSes. This counts the number of iterations where a satellite ID was in view of this GS
sat_counter_0 = Counter()
sat_counter_1 = Counter()

HOME_DIR = "../gen_data/starlink_550_isls_plus_grid_ground_stations_paris_grid_algorithm_free_one_only_over_isls/dynamic_state_600000ms_for_6000s"

sats_in_range_files = glob.glob(HOME_DIR + "/sats_in_range_of_*.txt")

iter = 0
# This prints the IDs of satellites in view of a given GS at each iteration. 
for sat_file in sats_in_range_files:
    with open(sat_file, "r") as f_in:
        print("------------iter %d -------------------" %(iter))
        for line in f_in:
            sat_ids = line.split(" ")[1:][1::2]
            gs_id = int(line.split(" ")[0].split(",")[0])
            print(sat_ids)
            if gs_id == 0:
                for sat_id in sat_ids:
                    sat_counter_0[sat_id] += 1 
            if gs_id == 1:
                for sat_id in sat_ids:
                    sat_counter_1[sat_id] += 1 
        iter += 1

print("--------------------- counter 0 ----------------")
print(sat_counter_0)
print("--------------------- counter 1 ----------------")
print (sat_counter_1)