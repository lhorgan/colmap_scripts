DATA_PATH="/mnt/Data4/luke/caves"
SCENE="Combined"

rm -rf "${DATA_PATH}/${SCENE}/sparse/text_placeholder"
mkdir -p "${DATA_PATH}/${SCENE}/sparse/text_placeholder"

#DATABASE_PATH="/home/luke/Documents/titanic/database"

echo "Creating initial placeholder text model"
time python3 create_db.py \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/sparse/text_placeholder \

echo "Running feature extractor"
time colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images