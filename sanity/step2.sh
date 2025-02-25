DATA_PATH=/home/luke/Documents/pamir_reconstructions/gps/gps_small_std_dev_3
SCENE=Pamir1kf

python3 write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --prior_position_std_x 3 \
    --prior_position_std_y 3 \
    --prior_position_std_z 3