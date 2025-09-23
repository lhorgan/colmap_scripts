#!/bin/bash
DATA_PATH=/home/luke/Documents/Ship/Back
SCENE=combo

# rm -rf "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
# rm -rf "${DATA_PATH}/${SCENE}/sparse/text"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text"

# touch "${DATA_PATH}/${SCENE}/database.db"

# echo "Running feature extractor"
# time colmap feature_extractor \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images

# echo "Running exhaustive matcher"
# time colmap exhaustive_matcher \
#     --database_path ${DATA_PATH}/${SCENE}/database.db

# colmap mapper \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images \
#     --output_path ${DATA_PATH}/${SCENE}/sparse

echo "Running conversion to text"
time python read_write_model.py \
    --input_model ${DATA_PATH}/${SCENE}/sparse \
    --input_format ".bin" \
    --output_model ${DATA_PATH}/${SCENE}/sparse/text \
    --output_format ".txt"