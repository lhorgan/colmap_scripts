DATA_PATH=$1
SCENE=$2

time colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images

time colmap exhaustive_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db
# time colmap sequential_matcher \
#     --database_path $DATA_PATH/$SCENE/output/database.db 