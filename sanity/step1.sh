DATA_PATH=/home/luke/Documents/pamir_reconstructions/gps/gps_small_std_dev_3
SCENE=Pamir1kf

python create_db_with_known_poses_224.py \
    --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output