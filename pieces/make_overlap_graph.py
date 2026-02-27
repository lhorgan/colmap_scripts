import os
import pickle
import open3d as o3d
import numpy as np

from plywood import write_point_cloud

class FancyList:
    def __init__(self):
        self.list = []
        self.set = set()
    
    def add(self, val):
        if val not in self.set:
            self.set.add(val)
            self.list.append(val)
    
    def contains(self, val):
        return val in self.set

    def as_list(self):
        return self.list

def dadd(dict, key, entry):
    if key not in dict:
        dict[key] = set()
    dict[key].add(entry)

def get_3D_point_key(scene, model, point3D_id):
    return f"{scene}-{model}-{point3D_id}"

def parse_3D_point_key(key):
    #print("KEY", key)
    scene, model, point3D_id = key.split("-")
    return scene, model, point3D_id

def get_2D_point_key(image_id, x, y):
    return f"{image_id}-{x[:6]}-{y[:6]}"

def get_model_key(scene, model):
    return f"{scene}-{model}"

def parse_model_key(key):
    scene, model = key.split("-")
    return scene, model

# def contains(sorted_list, x):
#     i = bisect.bisect_left(sorted_list, x)
#     return i < len(sorted_list) and sorted_list[i] == x

def make_overlap_graph(base_path):
    scenes = os.listdir(base_path)
    
    point3D_to_point2Ds = {}
    point2D_to_point3Ds = {}
    #point2D_to_model = {}

    for scene in scenes:
        print(f"Reading scene {scene}.")
        scene_dir = f"{base_path}/{scene}"
        models = os.listdir(f"{scene_dir}/sparse")
        for model in models:
            model_dir = f"{scene_dir}/sparse/{model}"
            
            # with open(f"{model_dir}/text/points3D.txt") as f:
            #     if line.startswith("#"):
            #         continue

            #     for line in f.readline():
            #         pass

            with open(f"{model_dir}/text/images.txt") as f:
                ctr = 0
                for line in f.readlines():
                    if line.startswith("#"):
                        continue
                    
                    if ctr % 2 == 0:
                        image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, name = line.split(" ")
                    else:
                        points2D = line.split(" ")
                        for i in range(0, len(points2D)-1, 3):
                            point3D_id = int(points2D[i+2])
                            if point3D_id != -1:
                                x = points2D[i]
                                y = points2D[i+1]
                                point2D_key = get_2D_point_key(image_id, x, y)
                                point3D_key = get_3D_point_key(scene, model, point3D_id)
                                model_key = get_model_key(scene, model)
                                dadd(point3D_to_point2Ds, point3D_key, point2D_key)
                                dadd(point2D_to_point3Ds, point2D_key, point3D_key)
                                #dadd(point2D_to_model, point2D_key, model_key)
                            
                    ctr += 1

    return point3D_to_point2Ds, point2D_to_point3Ds#, point2D_to_model

def read_3D_points(base_path, point3D_to_point2Ds, point2D_to_point3Ds):
    print("Reading the 3D points")

    scenes = os.listdir(base_path)

    point3Ds_by_model = {}
    point3D_ids_by_model = {}
    colors_by_model = {}

    for scene in scenes:
        print(f"Reading scene {scene}.")
        scene_dir = f"{base_path}/{scene}"
        models = os.listdir(f"{scene_dir}/sparse")
        for model in models:
            points = []
            point_ids = []
            colors = []

            model_dir = f"{scene_dir}/sparse/{model}"

            my_model_key = get_model_key(scene, model)
            
            with open(f"{model_dir}/text/points3D.txt") as f:
                for line in f.readlines():
                    if line.startswith("#"):
                        continue
                    
                    info = line.split(" ")
                    point3D_id, x, y, z, r, g, b = info[:7]
                    #print("R G B", r, b, g)
                    point3D_key = get_3D_point_key(scene, model, point3D_id)

                    points.append([x, y, z])
                    point_ids.append(point3D_id)
                    colors.append([max(min(int(c), 255), 0) for c in [r, g, b]])
                    #colors.append([255, 0, 255])
            
            key = get_model_key(scene, model)
            point3Ds_by_model[key] = points
            point3D_ids_by_model[key] = point_ids
            colors_by_model[key] = colors

    point3D_key_to_index = {}
    for key in point3D_ids_by_model:
        scene, model = parse_model_key(key)
        for i, point3D_id in enumerate(point3D_ids_by_model[key]):
            point3D_key = get_3D_point_key(scene, model, point3D_id)
            point3D_key_to_index[point3D_key] = i
    
    overlaps = {}
    for key in point3D_ids_by_model:
        scene, model = parse_model_key(key)

        print("Hi there")
        for i, point3D_id in enumerate(point3D_ids_by_model[key]):
            point3D_key = get_3D_point_key(scene, model, point3D_id)
            evidence_points = point3D_to_point2Ds[point3D_key]
            print("EVIDENCE POINTS", evidence_points)
            
            for point2D_key in evidence_points:
                other_point_3D_keys = point2D_to_point3Ds[point2D_key]
                #print("THE OTHER 3D POINTS", other_point_3D_keys)
                for other_point_3D_key in other_point_3D_keys:
                    other_scene, other_model, other_point3D_id = parse_3D_point_key(other_point_3D_key)
                    other_model_key = get_model_key(other_scene, other_model)
                    if other_model_key != key: 
                        dadd(overlaps, point3D_key, other_point_3D_key)
                        print(f"I {point3D_key} at index {point3D_key_to_index[point3D_key]} overlap with {other_point_3D_key} at index {point3D_key_to_index[other_point_3D_key]}")
        
        #break
    
    overlap_graph = {}

    for point3D_key in overlaps:
        my_scene, my_model, my_id = parse_3D_point_key(point3D_key)
        my_model_key = get_model_key(my_scene, my_model)
        my_index = point3D_key_to_index[point3D_key]

        for other_point3D_key in overlaps[point3D_key]:
            other_model, other_scene, other_id = parse_3D_point_key(other_point3D_key)
            other_model_key = get_model_key(other_model, other_scene)
            other_index = point3D_key_to_index[other_point3D_key]

            indexes = {}
            indexes[my_model_key] = my_index
            indexes[other_model_key] = other_index

            ordered_model_keys = sorted([my_model_key, other_model_key])
            overlap_key = ":".join(ordered_model_keys)
            model_key_0, model_key_1 = ordered_model_keys

            if overlap_key not in overlap_graph:
                overlap_graph[overlap_key] = (FancyList(), FancyList())
            
            index0 = indexes[model_key_0]
            index1 = indexes[model_key_1]

            if not overlap_graph[overlap_key][0].contains(index0) and not overlap_graph[overlap_key][1].contains(index1):
                overlap_graph[overlap_key][0].add(index0)
                overlap_graph[overlap_key][1].add(index1)
    
    return point3Ds_by_model, colors_by_model, overlap_graph

    # overlap_points = {}
    # for point3D_key in overlaps:
    #     my_scene, my_model, my_id = parse_3D_point_key(point3D_key)
    #     my_model_key = get_model_key(my_scene, my_model)
    #     my_index = point3D_key_to_index[point3D_key]

    #     for other_point3D_key in overlaps[point3D_key]:
    #         other_model, other_scene, other_id = parse_3D_point_key(other_point3D_key)
    #         other_model_key = get_model_key(other_model, other_scene)
    #         other_index = point3D_key_to_index[other_index]

    #         overlap_key_f = f"{my_model_key}->{other_model_key}"
    #         overlap_key_b = f"{other_model_key}->{my_model_key}"

    #         overlap_points[overlap_key_f][0].add(my_index)
    #         overlap_points[overlap_key_f][1].add(other_index)

# Makes ply files in false color, showing overlapping points
def make_plys(point3Ds_by_model, overlap_graph, coob_path):
    for model_key in point3Ds_by_model:
        points = np.array(point3Ds_by_model[model_key])
        colors = np.zeros(points.shape).astype(np.uint8)

        for overlap_key in overlap_graph:
            model_key0, model_key1 = overlap_key.split(":")
            if model_key0 == model_key:
                overlap_inds = overlap_graph[overlap_key][0].as_list()
                colors[overlap_inds] = [255, 0, 0]
            elif model_key1 == model_key:
                overlap_inds = overlap_graph[overlap_key][1].as_list()
                colors[overlap_inds] = [255, 0, 0]
                
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        scene, model = parse_model_key(model_key)
        write_point_cloud(pcd, f"{coob_path}/{scene}/sparse/{model}/{model_key}_false_color.ply")
        #write_point_cloud(points, f"{output_dir}/{model_key}.ply", colors)

def make_plys_color(point3Ds_by_model, colors_by_model, overlap_graph, coob_path):
    for model_key in point3Ds_by_model:
        points = np.array(point3Ds_by_model[model_key])
        colors = np.array(colors_by_model[model_key]).astype(np.float64) / 255.0 
        print(colors)             

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        scene, model = parse_model_key(model_key)
        write_point_cloud(pcd, f"{coob_path}/{scene}/sparse/{model}/{model_key}.ply")

if __name__ == "__main__":
    root_path = "/home/luke/Documents/caaves"
    coob_path = f"{root_path}/spheres"
    pickle_path = f"{root_path}/pickle"

    if not os.path.exists(pickle_path):
        print("Making the pickles.")
        point3D_to_point2Ds, point2D_to_point3Ds = make_overlap_graph(coob_path)

        os.mkdir(pickle_path)

        with open(f"{pickle_path}/point3D_to_point2Ds.pkl", "wb+") as f:
            pickle.dump(point3D_to_point2Ds, f)
        with open(f"{pickle_path}/point2D_to_model.pkl", "wb+") as f:
            pickle.dump(point2D_to_point3Ds, f)
    else:
        print("The pickles are already made.")
        with open(f"{pickle_path}/point3D_to_point2Ds.pkl", "rb") as f:
            point3D_to_point2Ds = pickle.load(f)
        with open(f"{pickle_path}/point2D_to_model.pkl", "rb") as f:
            point2D_to_point3Ds = pickle.load(f)

    point3Ds_by_model, colors_by_model, overlap_graph = read_3D_points(coob_path, point3D_to_point2Ds, point2D_to_point3Ds)

    overlaps_path = f"{pickle_path}/overlaps.pkl"

    with open(overlaps_path, "wb+") as f:
        pickle.dump([point3Ds_by_model, overlap_graph], f)
    
    make_plys(point3Ds_by_model, overlap_graph, coob_path)
    make_plys_color(point3Ds_by_model, colors_by_model, overlap_graph, coob_path)