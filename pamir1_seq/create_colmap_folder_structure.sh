#!/usr/bin/bash
#
# Description: Create structure for colmap scripts. Can concatenate multiple ones.
# Author: Alberto Quattrini Li (alberto.quattrini.li@dartmouth.edu)
#
#e.g., 
# bash create_colmap_folder_structure.sh /scratch/aql/pamir/colmap/ Pamir1kf_One_Target_Pamir2Trimkf_One_Target /scratch/data/pamir/Pamir1kf_One_Target,/scratch/data/pamir/Pamir2Trimkf_One_Target /scratch/data/pamir/svin_Pamir1Fixed_clean.txt,/scratch/data/pamir/svin_Pamir2TrimFixed_clean.txt
DATA_PATH=$1
SCENE=$2

# path containing images
INPUT_IMAGES_PATH=$3
INPUT_SVIN_PATH=$4

# script for inversion
INVERSION_SCRIPT_PATH="../pamir0/invert2.py"
APPENDIX="_inv"

#creating DATA_PATH
complete_path=$DATA_PATH/$SCENE
images_path=$complete_path/Images
svin_path=$complete_path/svin.txt

# TODO checks
mkdir -p $images_path
mkdir -p $complete_path/output/sparse
touch $svin_path

IFS=',' read -ra strings <<< "$INPUT_IMAGES_PATH"
for string in "${strings[@]}"; do
  ln -s $string/* $images_path
done
IFS=',' read -ra strings <<< "$INPUT_SVIN_PATH"
for string in "${strings[@]}"; do
  if [[ "$string" != *"$APPENDIX"* ]]; then
    string=$(python $INVERSION_SCRIPT_PATH $string)
    echo "inverted, $string"
  fi
  tail -n +2 $string >> $svin_path
done



