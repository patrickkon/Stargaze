# Usage help
if [ "$1" == "--help" ] || ([ "$#" != "2" ] && [ "$#" != "3" ] && [ "$#" != "4" ]); then
  echo "Usage: bash generate_for_paper.sh [id: 0 - 14] [number of threads] [duration (integer): seconds] [timestep (integer): milliseconds]"
  exit 0
fi

# Fetch arguments
id="$1"
num_threads=$2
# Optional arguments
duration=${3:-1}
timestep=${4:-1}

# Check validity of arguments
if [ "${id}" -lt "0" ] || [ "${id}" -gt "14" ]; then
  echo "Invalid workload id: ${id}"
  exit 1
fi
if [ "${num_threads}" -lt "0" ] || [ "${num_threads}" -gt "128" ]; then
  echo "Invalid number of threads: ${num_threads}"
  exit 1
fi

# Print what is being run
echo "Running workload ${id} with ${num_threads} threads"

# # Starlink-550 with ISLs
# if [ "${id}" = "6" ]; then
#   python extractor.py 6000 600000 isls_plus_grid ground_stations_paris_grid algorithm_free_one_only_over_isls ${num_threads}
# fi
# if [ "${id}" = "7" ]; then
#   python extractor.py 200 100 isls_plus_grid ground_stations_paris_grid algorithm_free_one_only_over_isls ${num_threads}
# fi
# if [ "${id}" = "8" ]; then
#   python extractor.py 200 1000 isls_plus_grid ground_stations_paris_moscow_grid algorithm_free_one_only_over_isls ${num_threads}
# fi
# For graph1 testing (i.e. everything prior to ISL reconfig):
if [ "${id}" = "9" ]; then
  python extractor.py ${duration} ${timestep} isls_custom ground_stations_top_100 algorithm_free_one_only_over_isls ${num_threads} 0
fi
# For testing +grid w/ ISL reconfig:
if [ "${id}" = "8" ]; then
  python extractor.py ${duration} ${timestep} isls_plus_grid ground_stations_top_100 algorithm_free_one_only_over_isls ${num_threads} 0
fi