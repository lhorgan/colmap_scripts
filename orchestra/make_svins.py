import os
from filter_svin import filter_svin
from colmap_to_svin import colmap_to_svin
from invert_svin import invert

def main():
    base_path = "/mnt/disk_1_ssd/luke/blub"
    svin_path = f"{base_path}/svin_raw/Combined.txt"
    bins_path = f"{base_path}/spheres"
    bin_dirnames = os.listdir(bins_path)
    for dirname in bin_dirnames:
        models = os.listdir(f"{bins_path}/{dirname}/sparse")
        for model in models:
            model_path = f"{bins_path}/{dirname}/sparse/{model}"

            colmap_output_path = f"{model_path}/svin_from_colmap.txt"
            colmap_output_path_inv = f"{model_path}/svin_from_colmap_inv.txt"
            images_set = colmap_to_svin(f"{model_path}/text/images.txt", colmap_output_path)
            invert(colmap_output_path, colmap_output_path_inv)
            filter_svin(input_path=svin_path, output_path=f"{model_path}/svin.txt", images_set=images_set)

if __name__ == "__main__":
    main()