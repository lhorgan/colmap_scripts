#!/bin/bash
# DATA_PATH=/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered
# SCENE=Tiny_no_poses

DATA_PATH=/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched
SCENE=Combined

# rm -rf "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
# rm -rf "${DATA_PATH}/${SCENE}/sparse/text"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text"

# echo "Creating initial placeholder text model"
# time python3 create_db_with_known_poses.py \
#     --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
#     --images_path ${DATA_PATH}/${SCENE}/Images \
#     --out_path $DATA_PATH/$SCENE/sparse/text_placeholder \

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