DATA_PATH=$1
SCENE=$2

echo $DATA_PATH
echo $SCENE

python python_scripts/create_db.py \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output