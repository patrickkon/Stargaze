# Main entry point for our use of hypatia plus
# Usage help
if [ "$1" == "--help" ]; then
  echo "Usage: bash main.sh [duration (integer): seconds] [timestep (integer): milliseconds]"
  exit 0
fi
num_threads=20
duration=${1:-600} #defaults to 10 minutes
timestep=${2:-60000} #defaults to 1 minute
# Check validity of arguments
# if [ "${id}" -lt "0" ] || [ "${id}" -gt "14" ]; then
#   echo "Invalid workload id: ${id}"
#   exit 1
# fi

# For graph1 testing (i.e. everything prior to ISL reconfig):
# bash generate_for_paper.sh 9 ${num_threads} ${duration} ${timestep} || exit 1

# For testing +grid w/ ISL reconfig:
bash generate_for_paper.sh 8 ${num_threads} ${duration} ${timestep} || exit 1