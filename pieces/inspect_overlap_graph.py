import pickle

from make_overlap_graph import FancyList

def inspect(pickle_path):
    pass

if __name__ == "__main__":
    root_path = "/home/luke/Documents/alts"
    pickle_path = f"{root_path}/pickle"
    overlaps_path = f"{pickle_path}/overlaps.pkl"

    # with open(f"{pickle_path}/point3D_to_point2Ds.pkl", "rb") as f:
    #     point3D_to_point2Ds = pickle.load(f)
    # with open(f"{pickle_path}/point2D_to_model.pkl", "rb") as f:
    #     point2D_to_point3Ds = pickle.load(f)
    with open(overlaps_path, "rb") as f:
        point3Ds_by_model, overlaps_graph = pickle.load(f)

    for overlap_key in overlaps_graph:
        print(overlap_key)