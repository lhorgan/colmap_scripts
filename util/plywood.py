import open3d as o3d
import numpy as np

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)

class PCSplitter():
    def __init__(self, pcd_path):
        self.pcd_path = pcd_path
        self.pcd = read_point_cloud(pcd_path)
        #self.align_bb()
        self.points = np.asarray(self.pcd.points)

    def align_bb(self):
        # Get original OBB
        obb_original = self.pcd.get_oriented_bounding_box()
        original_extent = obb_original.extent
        
        # Rotate and center
        pcd_rotated = self.pcd.rotate(obb_original.R.T, center=(0, 0, 0))
        pcd_rotated.translate(-pcd_rotated.get_center())
        self.pcd = pcd_rotated
        
        # Check the new AABB
        aabb = self.pcd.get_axis_aligned_bounding_box()
        new_extent = aabb.get_extent()
        
        print(f"Original OBB extent: {original_extent}")
        print(f"Aligned AABB extent: {new_extent}")
        print(f"Difference: {np.abs(original_extent - new_extent)}")

    def get_bounds(self):
        bb = self.pcd.get_axis_aligned_bounding_box()
        #print(bb)
        #print(self.pcd.get_oriented_bounding_box())

        min_x, min_y, min_z = bb.min_bound
        max_x, max_y, max_z = bb.max_bound
        return min_x, max_x, min_y, max_y, min_z, max_z
    
    def inds_to_key(self, x, y, z):
        return f"bin_{x}_{y}_{z}"

    def bin_points(self, bin_count, overlap_thresh=0.1):
        n = bin_count
        min_x, max_x, min_y, max_y, min_z, max_z = self.get_bounds()
        lx = max_x - min_x
        ly = max_y - min_y
        lz = max_z - min_z

        nx = ((n * lx**2) / (ly * lz))**(1/3)
        lb = lx / nx
        print("Length of a box", lb)
        print(lx / lb)
        print(ly / lb)
        print(lz / lb)

        bins = {}
        for x, y, z in self.points:
            bin_x = (x - min_x) / lb
            bin_y = (y - min_y) / lb
            bin_z = (z - min_z) / lb
            bin = [bin_x, bin_y, bin_z]
            
            for i in range(3):
                bin_i_int = int(bin[i])
                bin_i_dec = bin[i] - bin_i_int
                if bin_i_dec < overlap_thresh and bin[i] - 1 >= 0:
                    bin_int = [int(b) for b in bin]
                    bin_int[i] -= 1
                    bin_key = self.inds_to_key(*bin_int)
                    if bin_key not in bins:
                        bins[bin_key] = []
                    bins[bin_key].append([x, y, z])
            
            bin_key = self.inds_to_key(int(bin_x), int(bin_y), int(bin_z))
            if bin_key not in bins:
                bins[bin_key] = []
            bins[bin_key].append([x, y, z])
        
        total_len = 0
        for key in bins:
            #print(key, len(bins[key]))
            total_len += len(bins[key])
        
        self.bins = bins

        print(f"We have {len(self.bins)} bins.")
        return bins

    def write_bins(self, output_dir):
        for bin_key in self.bins:
            print("Writing bin ", bin_key)
            bin_points = self.bins[bin_key]
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(np.array(bin_points))
            write_point_cloud(pcd, f"{output_dir}/{bin_key}.ply")

def main():
    #splitter = PCSplitter("/home/luke/Documents/peace/LeftonRigLeft/pointcloud_2025-11-08_20-56-01.ply")
    splitter = PCSplitter("/home/luke/Documents/peace/LeftonRigLeft/pc_aligned.ply")
    splitter.bin_points(50, overlap_thresh=0.2)
    splitter.write_bins("/home/luke/Documents/peace/LeftonRigLeft/bins")

if __name__ == "__main__":
    main()