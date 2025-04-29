DATA_PATH=/home/luke/Documents/pamir_reconstructions/apr23/experiments_2/gps
SCENE=Pamir1kf

python3 write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1