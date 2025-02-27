DATA_PATH=/media/landa/pamir/recombined_full
SCENE=Pamir1kf

python create_db_with_known_poses_224.py \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output