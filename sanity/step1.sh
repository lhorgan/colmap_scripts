DATA_PATH=/home/luke/Documents/pamir_reconstructions/apr23/experiments_2/gps
SCENE=Pamir1kf

python create_db_with_known_poses_224.py \
    --cam_poses ${DATA_PATH}/${SCENE}/svin.txt \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --cam_poses_type svin