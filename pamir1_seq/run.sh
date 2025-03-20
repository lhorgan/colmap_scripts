DATA_PATH=/home/luke/Documents/pamir_reconstructions/feb28/full
SCENE=Pamir1kf

time ./step1.sh $DATA_PATH $SCENE
time ./step2.sh $DATA_PATH $SCENE
time ./step3.sh $DATA_PATH $SCENE