DATA_PATH=$1
SCENE=$2

echo $DATA_PATH
echo $SCENE

python create_db_with_known_poses_224.py \
    --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --cam_poses_type svin