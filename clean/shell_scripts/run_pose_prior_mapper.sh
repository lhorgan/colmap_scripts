DATA_PATH=$1
SCENE=$2

colmap pose_prior_mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \