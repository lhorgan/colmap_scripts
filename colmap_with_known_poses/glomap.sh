DATA_PATH=$1
SCENE=$2
CAM_POSES_TXT_NAME=$3

# https://colmap.github.io/faq.html#fix-intrinsics

# colmap mapper \
#     --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/Images/${SCENE} \
#     --input_path ${DATA_PATH}/colmap/${SCENE}/sparse/text \
#     --output_path ${DATA_PATH}/colmap/${SCENE}/sparse

colmap point_triangulator \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
    --image_path ${DATA_PATH}/Images/${SCENE} \
    --input_path ${DATA_PATH}/colmap/${SCENE}/sparse/text \
    --output_path ${DATA_PATH}/colmap/${SCENE}/sparse