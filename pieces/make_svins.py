import os
from filter_svin import filter_svin

def main():
    svin_path = "/mnt/Data3/luke/peace/LeftonRigLeft/svin_2025_11_08_20_58_23.txt"
    bins_path = "/mnt/Data3/luke/peace/coob"
    bin_dirnames = os.listdir(bins_path)
    for dirname in bin_dirnames:
        output_path = f"{bins_path}/{dirname}/svin.txt"
        images_path = f"{bins_path}/{dirname}/Images"
        filter_svin(svin_path, output_path, images_path)

if __name__ == "__main__":
    main()