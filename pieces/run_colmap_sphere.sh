DATA_PATH=$1
SCENE=$2

mkdir -p ${DATA_PATH}/${SCENE}/sparse

python filter_colmap_db.py \
        /home/luke/Documents/titanic/Combined/database.db \
        ${DATA_PATH}/${SCENE}/database.db \
        ${DATA_PATH}/${SCENE}/Images

colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

colmap mapper \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse