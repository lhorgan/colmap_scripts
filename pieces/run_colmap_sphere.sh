DATA_PATH=$1
SCENE=$2

mkdir -p ${DATA_PATH}/${SCENE}/sparse

time python filter_colmap_db_fast.py \
        /mnt/Data4/luke/caves/Combined/database.db \
        ${DATA_PATH}/${SCENE}/database.db \
        ${DATA_PATH}/${SCENE}/Images

time colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

time colmap mapper \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse

touch ${DATA_PATH}/${SCENE}/complete.txt