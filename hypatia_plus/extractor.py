import sys
import math
from main_helper import MainHelper
from config import config_generate_constellation
from config import HYPATIA_DIR
from config import CLUSTER_CONFIG
from config import CLUSTER_DIR

# Note: we are using starlink phase 1 shell 1 as the simulated constellation for now. 
main_helper = MainHelper(
    *config_generate_constellation()
)

def main():
    """At every N time steps (default to 1), we extract the satellite config at those time steps, and we notify the k8s scheduler"""
    args = sys.argv[1:]
    if len(args) != 7:
        print("Must supply exactly six arguments")
        print("Usage: python extractor.py [duration (s)] [time step (ms)] " # TODO: may need to add a start time arg. 
              "[isls_plus_grid / isls_custom / isls_none] "
              "[ground_stations_{top_100, paris_moscow_grid}] "
              "[algorithm_{free_one_only_over_isls, free_one_only_gs_relays, paired_many_only_over_isls}] "
              "[num threads]"
              "[is_reconfig]")
              # TODO: may need to add arg for k8s scheduler IP address
        exit(1)
    else:
        main_helper.calculate(
            "gen_data",
            CLUSTER_CONFIG,
            CLUSTER_DIR,
            int(args[0]),
            int(args[1]),
            args[2],
            args[3],
            args[4],
            int(args[5]),
            int(args[6]),
        )

        # TODO: read the satellite config here, or pass somewhere to the k8s scheduler, unless it reads from the files directly
        


if __name__ == "__main__":
    main()
