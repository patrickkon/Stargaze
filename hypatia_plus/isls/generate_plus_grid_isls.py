import os
from collections import defaultdict

def generate_plus_grid_isls(output_filename_isls, CLUSTER_DIR, CLUSTER_CONFIG, n_orbits, n_sats_per_orbit, is_reconfig, isl_shift, idx_offset=0):
    """
    Generate plus grid ISL file, taking into account the patched customizations of satellites specified in user-provided topo.txt within CLUSTER_CONFIG

    Assumptions: for each node in topo.txt, we assume topo.txt will include all links (unmodified and to be modified now) of that node 
    Note: generated ISL file consists of unidirectional links (i.e. the reverse of a link is not included, add it manually if needed)

    :param output_filename_isls     Output filename
    :param CLUSTER_DIR              Cluster parent directory
    :pararm CLUSTER_CONFIG          Cluster configuration file path relative to CLUSTER_DIR
    :param n_orbits:                Number of orbits
    :param n_sats_per_orbit:        Number of satellites per orbit
    :param isl_shift:               ISL shift between orbits (e.g., if satellite id in orbit is X,
                                    does it also connect to the satellite at X in the adjacent orbit)
    :param is_reconfig:             boolean. If true, this is a ISL reconfig, not generating ISLs from scratch
    :param idx_offset:              Index offset (e.g., if you have multiple shells)
    """

    if n_orbits < 3 or n_sats_per_orbit < 3:
        raise ValueError("Number of x and y must each be at least 3")

    TOPO_FILE = CLUSTER_DIR + "/" + CLUSTER_CONFIG["topo_file"]
    PROVIDED_NODE_TO_SAT_OR_GS_MAPPING_FILE = CLUSTER_DIR + "/" + CLUSTER_CONFIG["node_to_sat_or_gs_mapping_file"]
    # NUM_MASTERS = CLUSTER_CONFIG["num_masters"]
    # NUM_WORKERS = CLUSTER_CONFIG["num_workers"]
    # NUM_GS = CLUSTER_CONFIG["num_gs"]
    list_isls = []

    # Get mapping:
    mapping = defaultdict(int) # {node_name: corresponding_SAT_ID}
    with open(PROVIDED_NODE_TO_SAT_OR_GS_MAPPING_FILE, 'r') as mapping_file:
        for line in mapping_file:
            row = line.split()
            assert len(row) == 2
            node_name = row[0]
            sat_id = int(row[1])
            mapping[node_name] = sat_id

    defined_sat_ids = mapping.values()

    # This is a ISL reconfiguration. Get current isl.txt
    if (os.path.exists(output_filename_isls) and os.stat(output_filename_isls).st_size != 0) and is_reconfig == True:
        with open(output_filename_isls, 'r') as f:
            for row in f:
                isl_pair = row.split()
                assert len(isl_pair) == 2
                sat0 = int(isl_pair[0])
                sat1 = int(isl_pair[1])
                # Do not include links that involve SAT IDs defined by the user:
                if sat0 in defined_sat_ids and sat1 in defined_sat_ids:
                    continue
                list_isls.append((sat0, sat1))
    else: # This is a new ISL topology. Generate generic +grid isl.txt
        for i in range(n_orbits):
            for j in range(n_sats_per_orbit):
                sat = i * n_sats_per_orbit + j

                # Link to the next in the orbit
                sat_same_orbit = i * n_sats_per_orbit + ((j + 1) % n_sats_per_orbit)
                sat_adjacent_orbit = ((i + 1) % n_orbits) * n_sats_per_orbit + ((j + isl_shift) % n_sats_per_orbit)

                # Do not include links that involve SAT IDs defined by the user: 
                # i.e. only include links where less than 2 nodes of the link are not part of SAT IDs defined by the user
                if not (idx_offset + min(sat, sat_same_orbit) in defined_sat_ids and idx_offset + max(sat, sat_same_orbit) in defined_sat_ids):
                    # Same orbit
                    list_isls.append((idx_offset + min(sat, sat_same_orbit), idx_offset + max(sat, sat_same_orbit)))
                if not (idx_offset + min(sat, sat_adjacent_orbit) in defined_sat_ids and idx_offset + max(sat, sat_adjacent_orbit) in defined_sat_ids):
                    # Adjacent orbit
                    list_isls.append((idx_offset + min(sat, sat_adjacent_orbit), idx_offset + max(sat, sat_adjacent_orbit)))

    # SECTION: Add isls with new patched topology as indicated by files in CLUSTER_CONFIG:
    # Reconstruct topo.txt based on SAT IDs instead of user provided node names:
    with open(TOPO_FILE, 'r') as topos:
        for topo in topos:
            row = topo.split()
            assert len(row) == 2
            left = row[0]
            right = row[1]
            if "g" in left or "g" in right:
                continue
            if mapping[left] > mapping[right]:
                list_isls.append((mapping[right], mapping[left]))
            else:
                list_isls.append((mapping[left], mapping[right]))

    with open(output_filename_isls, 'w+') as f:
        for (a, b) in list_isls:
            f.write(str(a) + " " + str(b) + "\n")

    return list_isls
