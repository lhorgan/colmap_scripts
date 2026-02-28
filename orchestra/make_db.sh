DATA_PATH="/mnt/disk_1_ssd/luke/blub"
SCENE="Combined"

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

rm -rf "${DATA_PATH}/${SCENE}/output/sparse/text_placeholder"
mkdir -p "${DATA_PATH}/${SCENE}/output/sparse/text_placeholder"

rm -rf "${DATA_PATH}/${SCENE}/output/sparse/text"
mkdir -p "${DATA_PATH}/${SCENE}/output/sparse/text"

python3 python_scripts/create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/fake_svins/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --base_path $DATA_PATH/$SCENE \
    --text_model ${DATA_PATH}/${SCENE}/output/sparse/text_placeholder

echo "Writing pose priors to database"
python3 python_scripts/write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1

echo "Running feature extractor"
time colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images