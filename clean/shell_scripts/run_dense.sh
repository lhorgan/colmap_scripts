DATA_PATH=$1
SCENE=$2

# python3 delay.py

echo "Running image undistorter"

colmap image_undistorter \
    --image_path $DATA_PATH/$SCENE/Images \
    --input_path $DATA_PATH/$SCENE/output/sparse/0 \
    --output_path $DATA_PATH/$SCENE/output/dense \
    --output_type COLMAP \
    --max_image_size 960

echo "Running patch match stereo"

colmap patch_match_stereo \
    --workspace_path $DATA_PATH/$SCENE/output/dense \
    --workspace_format COLMAP \
    --PatchMatchStereo.geom_consistency true

echo "Running stereo fusion"

colmap stereo_fusion \
    --workspace_path $DATA_PATH/$SCENE/output/dense \
    --workspace_format COLMAP \
    --input_type geometric \
    --output_path $DATA_PATH/$SCENE/output/dense/fused.ply

echo "Running poisson mesher"

colmap poisson_mesher \
    --input_path $DATA_PATH/$SCENE/output/dense/fused.ply \
    --output_path $DATA_PATH/$SCENE/output/dense/meshed-poisson.ply