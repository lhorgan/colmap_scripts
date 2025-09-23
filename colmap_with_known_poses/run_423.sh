DATA_PATH=$1
SCENE=$2

# echo $DATA_PATH
# echo $SCENE

# DATA_PATH="/home/luke/Documents/Ship/Back"
# SCENE="seq0"

rm -rf "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
mkdir -p "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
rm -rf "${DATA_PATH}/${SCENE}/sparse/text"
mkdir -p "${DATA_PATH}/${SCENE}/sparse/text"

echo "Creating initial placeholder text model"
time python3 create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/sparse/text_placeholder \

echo "Running feature extractor"
time colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images

echo "Running exhaustive matcher"
time colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

echo "Running point triangulator"
time colmap point_triangulator \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse \
    --input_path ${DATA_PATH}/${SCENE}/sparse/text_placeholder

echo "Running conversion to text"
time python read_write_model.py \
    --input_model ${DATA_PATH}/${SCENE}/sparse \
    --input_format ".bin" \
    --output_model ${DATA_PATH}/${SCENE}/sparse/text \
    --output_format ".txt"

# echo "Running incremental model refiner"
# time colmap incremental_model_refiner \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images \
#     --output_path ${DATA_PATH}/${SCENE}/sparse \
#     --input_path ${DATA_PATH}/${SCENE}/sparse/text