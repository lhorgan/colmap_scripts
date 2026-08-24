DATA_PATH=$1
SCENE=$2
DATABASE_PATH=$3
# DATA_PATH=/media/luke/Data2/luke/blub_r
# SCENE=spheres
# DATABASE_PATH=/media/luke/Data2/luke/blub_r/Combined/database.db

mkdir -p ${DATA_PATH}/${SCENE}/sparse

time python filter_colmap_db_fast.py \
        $DATABASE_PATH \
        ${DATA_PATH}/${SCENE}/database.db \
        ${DATA_PATH}/${SCENE}/Images

echo "Running exhaustive matcher"
# time colmap spatial_matcher \
#     --database_path ${DATA_PATH}/${SCENE}/database.db
time colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/database.db

time colmap mapper \
    --database_path ${DATA_PATH}/${SCENE}/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/sparse

touch ${DATA_PATH}/${SCENE}/complete.txt