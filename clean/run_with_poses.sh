DATA_PATH=/home/luke/Documents/hell
SCENE=First500_poses

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/Svin"

positions=("LEFT" "CENTER" "RIGHT")
for position in "${positions[@]}"; do
    python3 python_scripts/filter_svin.py \
        --input "${DATA_PATH}/Svin/${position}.txt" \
        --output "${DATA_PATH}/${SCENE}/Svin/${position}.txt" \
        --images "${DATA_PATH}/${SCENE}/Images/${position}"
done

python3 python_scripts/create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${SCENE}/Svin \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --cam_poses_type svin

python3 python_scripts/write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1

time ./shell_scripts/features_and_matching.sh $DATA_PATH $SCENE
time ./shell_scripts/run_pose_prior_mapper.sh $DATA_PATH $SCENE
time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE