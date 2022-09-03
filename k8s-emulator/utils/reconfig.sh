#!/bin/bash

# Generate constellation data to be consumed by provision_tc_mod.py
# TODO: automate this. Currently users have to either use the default values (i.e. do not provide arguments to main.sh),
# or manually add them here (i.e. main.sh [duration] [timestep]) according to what they already defined in cluster_config.yaml
duration=$1 #seconds. make sure matches value in cluster_config.yaml
timestep=$2 #seconds. make sure matches value in cluster_config.yaml
timestep=$(($timestep * 1000)) # convert to milliseconds
bash -c "cd ../../../hypatia_plus; bash main.sh ${duration} ${timestep}"

# Config:
python3 utils/reconfig.py
python3 utils/provision_routes.py
python3 utils/provision_tc_mod.py