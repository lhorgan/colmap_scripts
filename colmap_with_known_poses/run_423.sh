DATA_PATH=/home/luke/Documents/pamir_reconstructions/apr23/experiments_2/point_tri_then_inc_ref_2
SCENE=Pamir1kf

# rm -rf "${DATA_PATH}/${SCENE}/sparse/text"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text"

# python3 create_db_with_known_poses.py \
#     --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
#     --images_path ${DATA_PATH}/${SCENE}/Images \
#     --out_path $DATA_PATH/$SCENE/sparse/text \

# colmap feature_extractor \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images

# colmap exhaustive_matcher \
#         --database_path ${DATA_PATH}/${SCENE}/database.db

#colmap point_triangulator \
colmap incremental_model_refiner \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse \
    --input_path ${DATA_PATH}/${SCENE}/sparse/text