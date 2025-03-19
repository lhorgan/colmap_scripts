DATA_PATH=/home/luke/Documents/pamir_reconstructions/small_multi_test
SCENE=Pamir1kf

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

./shell_scripts/create_db.sh $DATA_PATH $SCENE
time ./shell_scripts/features_and_matching.sh $DATA_PATH $SCENE
time ./shell_scripts/run_glomap.sh $DATA_PATH $SCENE
time ./shell_scripts/run_dense.sh $DATA_PATH $SCENE