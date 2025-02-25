DATA_PATH=/home/luke/Documents/pamir_reconstructions/gps/gps_small
SCENE=Pamir1kf

python3 write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt