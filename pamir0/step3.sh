DATA_PATH=/media/landa/pamir/recombined_full
SCENE=Pamir1kf

time colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images

# Alternative for larger  datasets: spatial_matcher
time colmap sequential_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db 

time colmap mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \