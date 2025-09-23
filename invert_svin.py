import numpy as np
from scipy.spatial.transform import Rotation
from scipy.linalg import null_space

def create_pose_matrix(tx, ty, tz, qx, qy, qz, qw):
    """Create 4x4 pose matrix from translation and quaternion"""
    P = np.eye(4)
    
    # Set rotation part (3x3)
    #P[:3,:3] = Rotation.from_quat([qx, qy, qz, qw])
    r = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    #print(r)
    P[:3,:3] = r
    
    # Set translation part (3x1)
    P[:3,3] = [tx, ty, tz]
    
    return P

def invert(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()
    
    comment = lines[0]

    with open(output_path, "w+") as f:
        f.write(comment)
        
        for line in lines[0:]:
            if line.startswith("#"):
                continue

            timestamp = line.split(" ")[0]
            pose = [float(x) for x in (line.split(" ")[1:])]
            p = create_pose_matrix(tx=pose[0], ty=pose[1], tz=pose[2], qx=pose[3], qy=pose[4], qz=pose[5], qw=pose[6])
            
            pose_null_space = null_space(p[:3])
            
            p_inv = np.linalg.inv(p)
            
            R = p_inv[:3, :3]
            T = p_inv[:3, 3]
            q = Rotation.from_matrix(R).as_quat()

            C = pose_null_space[:3] / pose_null_space[3]
            print(C)
            print(T)
            print("\n\n")
        
            f.write(f"{timestamp} {T[0]:.10f} {T[1]:.10f} {T[2]:.10f} {q[0]:.10f} {q[1]:.10f} {q[2]:.10f} {q[3]:.10f}\n")

# Usage: first arg is the path to the original file
# Output: first arg is the path where you want the inverted file to  be saved
#invert("/home/luke/Documents/hell/may27/Svin_non_inv/Center.txt", "/home/luke/Documents/hell/may27/Svin/Center.txt")
#invert("/home/luke/Documents/hell/may27/Svin_non_inv/Left.txt", "/home/luke/Documents/hell/may27/Svin/Left.txt")
#invert("/home/luke/Documents/hell/may27/Svin_non_inv/Right.txt", "/home/luke/Documents/hell/may27/Svin/Right.txt")

# invert("/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir0/Pamir0_transformed.txt", "/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir0/svin.txt")
# invert("/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir1/Pamir1_transformed.txt", "/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir1/svin.txt")
# invert("/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir2/Pamir2_transformed.txt", "/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir2/svin.txt")

# invert("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1_and_Pamir2/svin_non_inv.txt", "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1_and_Pamir2/svin.txt")
invert("/home/luke/pamir/Pamir2/Pamir2_in_Pamir1_miraculously.txt", "/home/luke/pamir/Pamir2/Pamir2_in_Pamir1_miraculously_inv.txt")