DATA_PATH=/home/luke/Documents/pamir_stuff/gps/gps_small_with_svin_poses_cartesian
SCENE=Pamir1kf

colmap feature_extractor \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images

# Alternative for larger datasets: spatial_matcher
colmap exhaustive_matcher \
    --database_path $DATA_PATH/$SCENE/output/database.db 

colmap pose_prior_mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \