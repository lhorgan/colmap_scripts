import numpy as np

class Pipeline:
    def __init__(self, svin_path):
        self.svin_path = svin_path
        self.poses = {}

    def read_svin_file(self):
        with open(self.svin_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                timestamp = line.split(" ")[0]
                image_name = f"{timestamp.replace('.', '')}.png"
                pose = [float(x) for x in (line.split(" ")[1:])]
                self.poses[image_name] = pose
    
    def get_cam_centers(self):
        cam_centers = np.zeros((len(self.poses), 3))
        i = 0
        for image_name in self.poses:
            pose = self.poses[image_name]
            cam_centers[i] = np.array(pose[:3])
            i += 1
        return cam_centers

    def get_bounds(self, points):
        min_x = np.min(points[:,0])
        max_x = np.max(points[:,0])

        min_y = np.min(points[:,1])
        max_y = np.max(points[:,1])

        min_z = np.min(points[:,2])
        max_z = np.max(points[:,2])

        return [min_x, max_x, min_y, max_y, min_z, max_z]

pipeline = Pipeline("/home/luke/Documents/datasets/svin_LeftOnRig_Depth_introduced.txt")
pipeline.read_svin_file()
points = pipeline.get_cam_centers()

print(points)

bounds = pipeline.get_bounds(points)
print(bounds)


