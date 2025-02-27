DATA_PATH=/home/luke/Documents/pamir_stuff/gps/gps_small_with_svin_poses_cartesian
SCENE=Pamir1kf

python create_db_with_known_poses_224.py \
    --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --cam_poses_type svin