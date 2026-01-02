import os
import pickle

def dadd(dict, key, entry):
    if key not in dict:
        dict[key] = set()
    dict[key].add(entry)

def get_3D_point_key(scene, model, point3D_id):
    return f"{scene}_{model}_{point3D_id}"

def get_2D_point_key(image_id, x, y):
    return f"{image_id}_{x[:6]}_{y[:6]}"

def get_model_key(scene, model):
    return f"{scene}_{model}"

def make_overlap_graph(base_path):
    scenes = os.listdir(base_path)
    
    point3D_to_point2Ds = {}
    point2D_to_model = {}

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
                                dadd(point2D_to_model, point2D_key, model_key)
                            
                    ctr += 1

    return point3D_to_point2Ds, point2D_to_model

def read_3D_points(base_path, point3D_to_point2Ds, point2D_to_model):
    scenes = os.listdir(base_path)

    for scene in scenes:
        print(f"Reading scene {scene}.")
        scene_dir = f"{base_path}/{scene}"
        models = os.listdir(f"{scene_dir}/sparse")
        for model in models:
            model_dir = f"{scene_dir}/sparse/{model}"

            my_model_key = get_model_key(scene, model)
            
            with open(f"{model_dir}/text/points3D.txt") as f:
                for line in f.readlines():
                    if line.startswith("#"):
                        continue
                    
                    info = line.split(" ")
                    point3D_id, x, y, z, r, g, b = info[:7]
                    point3D_key = get_3D_point_key(scene, model, point3D_id)
                    evidence_points = point3D_to_point2Ds[point3D_key]
                    for point2D_key in evidence_points:
                        models_2D_point_appears_in = point2D_to_model[point2D_key]
                        other_models = models_2D_point_appears_in - set([my_model_key])
                        if len(other_models) == 0:
                            print("THIS POINT IS ALL ALONE")
                        for their_model_key in other_models:
                            print(f"3D point {x},{y},{z} in {my_model_key} also appears in {their_model_key}")

if __name__ == "__main__":
    root_path = "/home/luke/Documents/peace2/peace"
    coob_path = f"{root_path}/coob"
    pickle_path = f"{root_path}/pickle"

    if not os.path.exists(pickle_path):
        print("Making the pickles.")
        point3D_to_point2Ds, point2D_to_model = make_overlap_graph(coob_path)

        with open(f"{pickle_path}/point3D_to_point2Ds.pkl", "wb+") as f:
            pickle.dump(point3D_to_point2Ds, f)
        with open(f"{pickle_path}/point2D_to_model.pkl", "wb+") as f:
            pickle.dump(point2D_to_model, f)
    else:
        print("The pickles are already made.")
        with open(f"{pickle_path}/point3D_to_point2Ds.pkl", "rb") as f:
            point3D_to_point2Ds = pickle.load(f)
        with open(f"{pickle_path}/point2D_to_model.pkl", "rb") as f:
            point2D_to_model = pickle.load(f)

    read_3D_points(coob_path, point3D_to_point2Ds, point2D_to_model)

    