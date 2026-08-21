# To start, BASE_PATH must contain Combined and svin_raw
# Combined should have Images, and svin_raw should have 
# Center.txt, Left.txt, Right.txt

BASE_PATH="/media/luke/Data2/luke/blub_r"

# python make_cave_spheres.py \
#     --svin_path="$BASE_PATH/svin_raw/Center.txt" \
#     --images_path="$BASE_PATH/Combined/Images" \
#     --dst_path="$BASE_PATH/spheres" \
#     --unexpanded_clusters_path="$BASE_PATH/unexpanded_clusters.pkl"

# mkdir $BASE_PATH/fake_svins

# python make_fake_svins.py \
#     --svin_center_path="$BASE_PATH/svin_raw/Center.txt" \
#     --svin_left_path="$BASE_PATH/svin_raw/Left.txt" \
#     --svin_right_path="$BASE_PATH/svin_raw/Right.txt" \
#     --output_path="$BASE_PATH/fake_svins"

# python combine_svins.py \
#     --svin_files "$BASE_PATH/fake_svins/Center.txt" "$BASE_PATH/fake_svins/Left.txt" "$BASE_PATH/fake_svins/Right.txt" \
#     --output "$BASE_PATH/fake_svins/svin.txt"

# ./make_db.sh $BASE_PATH "Combined"

python lights.py \
    --spheres_path="$BASE_PATH/spheres" \
    --database_path="$BASE_PATH/Combined/database.db"

# python make_text_models.py "$BASE_PATH/spheres"

# python make_overlap_graph.py \
#     --spheres_path="$BASE_PATH/spheres" \
#     --pickle_path="$BASE_PATH/pickle"

# python make_svins.py \
#     --svin_path="$BASE_PATH/svin_raw/Combined.txt" \
#     --bins_path="$BASE_PATH/spheres"