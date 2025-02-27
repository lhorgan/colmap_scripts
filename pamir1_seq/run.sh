# DATA_PATH=/media/landa/pamir/poses_test_small
# SCENE=Pamir1kf

# echo "!!!Starting small test!!!"

# #time ./step1.sh $DATA_PATH $SCENE
# #time ./step2.sh $DATA_PATH $SCENE
# #time ./step3.sh $DATA_PATH $SCENE

# echo "!!!Concluding small test!!!"

DATA_PATH=/media/landa/pamir/recombined_full_with_poses
SCENE=Pamir1kf

echo "!!!Starting no targets with poses!!!"

#time ./step1.sh $DATA_PATH $SCENE
#time ./step2.sh $DATA_PATH $SCENE
time ./step3.sh $DATA_PATH $SCENE

echo "!!!Concluding no targets with poses!!!"

#################################################3

DATA_PATH=/media/landa/pamir/all_images_with_poses
SCENE=Pamir1kf

echo "!!!Starting all with poses!!!"

#time ./step1.sh $DATA_PATH $SCENE
#time ./step2.sh $DATA_PATH $SCENE
time ./step3.sh $DATA_PATH $SCENE

echo "!!!Concluding all with poses!!!"

##################################################3