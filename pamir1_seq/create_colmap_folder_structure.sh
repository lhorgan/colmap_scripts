#!/usr/bin/bash
#
# Description: Create structure for colmap scripts.
# Author: Alberto Quattrini Li (alberto.quattrini.li@dartmouth.edu)
#
#e.g., 
# bash create_colmap_folder_structure.sh ~/colmap/pamir/ Pamir1kf_One_Target ~/data/Pamir1kf_One_Target ~/data/Pamir1kf_One_Target_svin.txt
DATA_PATH=$1
SCENE=$2

# path containing images
INPUT_IMAGES_PATH=$3
INPUT_SVIN_PATH=$4

#creating DATA_PATH
COMPLETE_PATH=$DATA_PATH/$SCENE

mkdir -p $COMPLETE_PATH
mkdir -p $COMPLETE_PATH/output/sparse

ln -s $INPUT_IMAGES_PATH $COMPLETE_PATH/Images
ln -s $INPUT_SVIN_PATH $COMPLETE_PATH/svin.txt



