DATA_PATH=/home/harish/Documents/catacombs_2
SCENE=catacombs_1_cam_order

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

./shell_scripts/create_db.sh $DATA_PATH $SCENE
echo "Running feature matching"
time ./shell_scripts/features_and_matching.sh $DATA_PATH $SCENE
echo "Running GLOMAP"
time ./shell_scripts/run_glomap.sh $DATA_PATH $SCENE
echo "Running dense"
time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE
