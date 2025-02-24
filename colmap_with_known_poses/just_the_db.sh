#!/bin/bash

DATA_PATH=$1
SCENE=$2
CAM_POSES_TXT_NAME=$3
# point threshold parameters
MAX_ERROR=2.0
MIN_TRACK_LEN=3

# create sparse model output paths
if [ ! -d "$DATA_PATH/colmap/${SCENE}/sparse/text" ]; then
  mkdir -p "$DATA_PATH/colmap/${SCENE}/sparse/text"
fi

# create database.db file
if [ -f "$DATA_PATH/colmap/${SCENE}/database.db" ]; then
    rm "$DATA_PATH/colmap/${SCENE}/database.db"
fi
touch "$DATA_PATH/colmap/${SCENE}/database.db"

# create cameras file encoding the calibrated intrinsics for our camera
python3 create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${CAM_POSES_TXT_NAME} \
    --images_path ${DATA_PATH}/Images/${SCENE} \
    --out_path ${DATA_PATH}/colmap/${SCENE}/sparse/text