DATA_PATH=/home/luke/Documents/pamir_reconstructions/small
SCENE=Pamir1kf

./step1.sh $DATA_PATH $SCENE
time ./step3.sh $DATA_PATH $SCENE