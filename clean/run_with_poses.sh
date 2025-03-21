DATA_PATH=/home/luke/Documents/pamir_reconstructions/small_multi_test
SCENE=Pamir1kf

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

./shell_scripts/create_db.sh $DATA_PATH $SCENE

python3 write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1

time ./shell_scripts/features_and_matching.sh $DATA_PATH $SCENE
time ./shell_scripts/pose_prior_mapper.sh $DATA_PATH $SCENE
time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE