DATA_PATH=/home/luke/Documents/pamir_stuff/gps/gps_small_with_svin_poses_cartesian
SCENE=Pamir1kf

python3 python_scripts/write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1