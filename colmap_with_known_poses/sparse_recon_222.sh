DATA_PATH=$1
SCENE=$2

create database.db file
if [ -f "${DATA_PATH}/${SCENE}/database.db" ]; then
    rm "${DATA_PATH}/${SCENE}/database.db"
fi
touch "${DATA_PATH}/${SCENE}/database.db"

colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images/

colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

colmap point_triangulator \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images/ \
    --input_path ${DATA_PATH}/${SCENE}/input/text \
    --output_path ${DATA_PATH}/${SCENE}/output/

colmap bundle_adjuster \
    --input_path ${DATA_PATH}/${SCENE}/output/ \
    --output_path ${DATA_PATH}/${SCENE}/output_refined/ \
    --BundleAdjustment.refine_extrinsics 1