#!/bin/bash
DATA_PATH=$1
SCENE=$2
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

colmap feature_extractor \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
    --image_path ${DATA_PATH}/Images/${SCENE}

colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db

# colmap mapper \
#     --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/Images/${SCENE} \
#     --output_path ${DATA_PATH}/colmap/${SCENE}/sparse