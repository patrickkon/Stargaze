#!/bin/bash

# Script specifically for setting up GS nodes

# Install helm package:
bash get-helm-3.sh

# # Setup python :
# # Create and activate conda environment, and install python 3.7.7
# wget -O temp.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# sh ./temp.sh
# rm ./temp.sh
# conda create --name stargaze-env python=3.7.7
# conda activate stargaze-env