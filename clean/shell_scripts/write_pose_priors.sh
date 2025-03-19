DATA_PATH=$1
SCENE=$2

python3 python_scripts/write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/output/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1