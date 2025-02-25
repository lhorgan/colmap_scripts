DATA_PATH=/home/luke/Documents/pamir_reconstructions/feb24/full
SCENE=Pamir0kf

colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images

# Alternative for larger datasets: spatial_matcher
colmap exhaustive_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db 

colmap mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \