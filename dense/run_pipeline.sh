DATA_PATH=/mnt/disk_1_ssd/luke/areas
SCENE=$1

echo "Running pipeline for scene: $SCENE"

rm -rf "${DATA_PATH}/${SCENE}/output"
mkdir -p "${DATA_PATH}/${SCENE}/output"

mkdir -p "${DATA_PATH}/${SCENE}/Svin"
mkdir -p "${DATA_PATH}/${SCENE}/Svin_Inv"

rm -rf "${DATA_PATH}/${SCENE}/output/sparse/text_placeholder"
mkdir -p "${DATA_PATH}/${SCENE}/output/sparse/text_placeholder"

rm -rf "${DATA_PATH}/${SCENE}/output/sparse/text"
mkdir -p "${DATA_PATH}/${SCENE}/output/sparse/text"

positions=("Left" "Center" "Right")
for position in "${positions[@]}"; do
    python3 python_scripts/filter_svin.py \
        --input "${DATA_PATH}/Svin/${position}.txt" \
        --output "${DATA_PATH}/${SCENE}/Svin/${position}.txt" \
        --images "${DATA_PATH}/${SCENE}/Images/${position}"
done

positions=("Left" "Center" "Right")
for position in "${positions[@]}"; do
    python3 python_scripts/invert_svin.py \
        --input "${DATA_PATH}/${SCENE}/Svin/${position}.txt" \
        --output "${DATA_PATH}/${SCENE}/Svin_Inv/${position}.txt"
done

python3 python_scripts/create_db_with_known_poses.py \
    --cam_poses ${DATA_PATH}/${SCENE}/Svin \
    --cam_poses_inv ${DATA_PATH}/${SCENE}/Svin_Inv \
    --images_path ${DATA_PATH}/${SCENE}/Images \
    --out_path $DATA_PATH/$SCENE/output \
    --base_path $DATA_PATH/$SCENE \
    --text_model ${DATA_PATH}/${SCENE}/output/sparse/text_placeholder

echo "Writing pose priors to database"
python3 python_scripts/write_pose_priors_to_database.py \
    --database_path $DATA_PATH/$SCENE/database.db \
    --pose_priors_path $DATA_PATH/$SCENE/output/poses.txt \
    --coordinate_system 1 \
    --prior_position_std_x 1 \
    --prior_position_std_y 1 \
    --prior_position_std_z 1

echo "Running feature extractor"
time colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images

echo "Running spatial matcher"
time colmap spatial_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

echo "Running point triangulator"
time colmap point_triangulator \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/output/sparse \
    --input_path ${DATA_PATH}/${SCENE}/output/sparse/text_placeholder

echo "Running conversion to text"
time python python_scripts/read_write_model.py \
    --input_model ${DATA_PATH}/${SCENE}/output/sparse \
    --input_format ".bin" \
    --output_model ${DATA_PATH}/${SCENE}/output/sparse/text \
    --output_format ".txt"

#echo "Copying original data for backup"
#cp -r ${DATA_PATH}/${SCENE} ${DATA_PATH}/${SCENE}_backup

echo "Running incremental model refiner"
time colmap incremental_model_refiner \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/output/sparse \
    --input_path ${DATA_PATH}/${SCENE}/output/sparse/text

time colmap image_undistorter \
    --image_path $DATA_PATH/$SCENE/Images \
    --input_path $DATA_PATH/$SCENE/output/sparse \
    --output_path $DATA_PATH/$SCENE/output/dense \
    --output_type COLMAP \
    --max_image_size 960

echo "Running patch match stereo"

time colmap patch_match_stereo \
    --workspace_path $DATA_PATH/$SCENE/output/dense \
    --workspace_format COLMAP \
    --PatchMatchStereo.geom_consistency true

echo "Running stereo fusion"

time colmap stereo_fusion \
    --workspace_path $DATA_PATH/$SCENE/output/dense \
    --workspace_format COLMAP \
    --input_type geometric \
    --output_path $DATA_PATH/$SCENE/output/dense/fused.ply

echo "Running poisson mesher"

time colmap poisson_mesher \
    --input_path $DATA_PATH/$SCENE/output/dense/fused.ply \
    --output_path $DATA_PATH/$SCENE/output/dense/meshed-poisson.ply