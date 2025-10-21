# DATA_PATH=$1
# SCENE=$2
DATA_PATH="/mnt/Data3/luke/xmas"
SCENE="Combined"

# rm -rf "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
# mkdir -p "${DATA_PATH}/${SCENE}/sparse/text_placeholder"

# echo "Creating initial placeholder text model"
# time python3 create_db.py \
#     --images_path ${DATA_PATH}/${SCENE}/Images \
#     --out_path $DATA_PATH/$SCENE/sparse/text_placeholder \

# echo "Running feature extractor"
# time colmap feature_extractor \
#     --database_path ${DATA_PATH}/${SCENE}/database.db \
#     --image_path ${DATA_PATH}/${SCENE}/Images

# echo "Running exhaustive matcher"
# time colmap exhaustive_matcher \
#     --database_path ${DATA_PATH}/${SCENE}/database.db

colmap mapper \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse

echo "Running conversion to text"
mkdir -p "${DATA_PATH}/${SCENE}/sparse/text"
time python read_write_model.py \
    --input_model ${DATA_PATH}/${SCENE}/sparse/0 \
    --input_format ".bin" \
    --output_model ${DATA_PATH}/${SCENE}/sparse/text \
    --output_format ".txt"

echo "Running conversion to ply"
colmap model_converter \
    --input_path="${DATA_PATH}/${SCENE}/sparse/0" \
    --output_path="${DATA_PATH}/${SCENE}/sparse0.ply" \
    --output_type="ply"

touch "${DATA_PATH}/${SCENE}/complete.txt"
