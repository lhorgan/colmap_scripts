import numpy as np
from scipy.spatial.transform import Rotation

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
        
        for line in lines[1:]:
            timestamp = line.split(" ")[0]
            pose = [float(x) for x in (line.split(" ")[1:])]
            p = create_pose_matrix(tx=pose[0], ty=pose[1], tz=pose[2], qx=pose[3], qy=pose[4], qz=pose[5], qw=pose[6])
            
            p_inv = np.linalg.inv(p)
            
            R = p_inv[:3, :3]
            T = p_inv[:3, 3]
            q = Rotation.from_matrix(R).as_quat()
        
            f.write(f"{timestamp} {T[0]:.10f} {T[1]:.10f} {T[2]:.10f} {q[0]:.10f} {q[1]:.10f} {q[2]:.10f} {q[3]:.10f}\n")

invert("/home/luke/Documents/pamir/underwater_data/pamir/svin_Pamir1_revised.txt", "/home/luke/Documents/pamir/underwater_data/pamir/svin_Pamir1_revised_inv.txt")