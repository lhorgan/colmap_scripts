DATA_PATH=/home/luke/Documents/pamir_reconstructions/small
SCENE=Pamir1kf

time glomap mapper \
    --database_path $DATA_PATH/$SCENE/output/database.db  \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path $DATA_PATH/$SCENE/output/sparse \