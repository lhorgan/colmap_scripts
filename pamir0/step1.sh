DATA_PATH=/home/luke/Documents/pamir_reconstructions/feb24/full
SCENE=Pamir0kf

python create_db_with_known_poses_224.py \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output