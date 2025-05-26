#!/bin/bash

DATA_PATH=/home/luke/Documents/hell
SCENE=First100

rm -rf "${DATA_PATH}/${SCENE}/output"

mkdir -p "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output/sparse/text_placeholder"
mkdir -p "${DATA_PATH}/${SCENE}/Svin"

positions=("Left" "Center" "Right")
for position in "${positions[@]}"; do
    python3 python_scripts/filter_svin.py \
        --input "${DATA_PATH}/Svin/${position}.txt" \
        --output "${DATA_PATH}/${SCENE}/Svin/${position}.txt" \
        --images "${DATA_PATH}/${SCENE}/Images/${position}"
done

python3 python_scripts/create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${SCENE}/Svin \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output/sparse \
    --cam_poses_type svin \
    --text_model $DATA_PATH/${SCENE}/output/sparse/text_placeholder

echo "Running feature extractor"
time colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images

echo "Running point triangulator"
time colmap point_triangulator \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/output/sparse \
    --input_path $DATA_PATH/${SCENE}/output/sparse/text_placeholder

# echo "Running incremental model refiner"
# time colmap incremental_model_refiner \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images \
#     --output_path ${DATA_PATH}/${SCENE}/output/sparse \
#     --input_path $DATA_PATH/${SCENE}/output/sparse/text_placeholder

#time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE