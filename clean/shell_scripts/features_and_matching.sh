DATA_PATH=$1
SCENE=$2

time colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --ImageReader.single_camera_per_folder 1 # Necessary?

# time colmap exhaustive_matcher \
#     --database_path $DATA_PATH/$SCENE/output/database.db
time colmap sequential_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db 