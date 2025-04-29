DATA_PATH=/home/luke/Documents/hell
SCENE=First500_poses

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

python3 python_scripts/create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${SCENE}/Svin \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --cam_poses_type svin

time ./shell_scripts/features_and_matching.sh $DATA_PATH $SCENE

colmap point_triangulator \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --input_path ${DATA_PATH}/${SCENE}/sparse/text \
    --output_path ${DATA_PATH}/${SCENE}/sparse \

time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE