DATA_PATH=$1
SCENE=$2

time colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images

# Alternative for larger datasets: spatial_matcher
time colmap exhaustive_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db 