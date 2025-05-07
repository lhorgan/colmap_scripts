DATA_PATH=$1
SCENE=$2

mkdir -p $DATA_PATH/$SCENE/output/sparse

colmap pose_prior_mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \
    --input_path ${DATA_PATH}/${SCENE}/sparse/text_placeholder