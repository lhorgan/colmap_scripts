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
    
    return np.linalg.inv(P)

def plot_cameras(cam_path, scale, output_file):
    #cams = read_cams_sfm(cam_path)
    # P = cams[:num_cams,0] # Num_Cams x 4 x 4
    # K = cams[:num_cams,1, :3, :3] # Num_Cams x 3 x 3
    
    with open(cam_path) as f:
        cam_lines = f.readlines()[1:]
    num_cams = len(cam_lines)

    P = np.zeros([num_cams, 4, 4])
    K = np.zeros([num_cams, 3, 3])

    # hard code these for now
    f = 590.3481895498027
    cx = 480
    cy = 270

    for i, line in enumerate(cam_lines):
        #print(line)
        pose = [float(x) for x in (line.split(" ")[1:])]
        #print(pose)
        p = create_pose_matrix(tx=pose[0], ty=pose[1], tz=pose[2], qx=pose[3], qy=pose[4], qz=pose[5], qw=pose[6])
        #print(p)
        #print(P[i])
        P[i] = p
        K[i] = np.array([[f, 0, cx],
                         [0, f, cy],
                         [0, 0, 1]])

    # build list of camera pyramid points
    pyr_pts = []
    for k,p in zip(K,P):
        fx = k[0,0]
        fy = k[1,1]
        cx = k[0,2]
        cy = k[1,2]
        pyr_pt = build_cam_pyr(scale, fx, fy, cx, cy)
        pp = np.linalg.inv(p) @ pyr_pt
        pyr_pts.append((pp, 1))

    # build point cloud using camera centers
    build_pyr_point_cloud(pyr_pts, output_file)

    return

def camera_cross(p, theta=0.5, t=15):
    x_rot_up = np.asarray([[1,0,0], [0,np.cos(-theta), -np.sin(-theta)],[0,np.sin(-theta),np.cos(-theta)]])
    x_rot_down = np.asarray([[1,0,0], [0,np.cos(theta), -np.sin(theta)],[0,np.sin(theta),np.cos(theta)]])

    y_rot_right = np.asarray([[np.cos(theta),0,np.sin(theta)], [0,1,0],[-np.sin(theta),0,np.cos(theta)]])
    y_rot_left = np.asarray([[np.cos(-theta),0,np.sin(-theta)], [0,1,0],[-np.sin(-theta),0,np.cos(-theta)]])
    
    p_top = np.copy(p)
    p_top[:3,:3] = x_rot_down @ p_top[:3,:3]
    p_top[1,3] += t
    p_top[2,3] += 5

    p_right = np.copy(p)
    p_right[:3,:3] = y_rot_left @ p_right[:3,:3]
    p_right[0,3] += t
    p_right[2,3] += 5

    p_bottom = np.copy(p)
    p_bottom[:3,:3] = x_rot_up @ p_bottom[:3,:3]
    p_bottom[1,3] -= t
    p_bottom[2,3] += 5


    p_left = np.copy(p)
    p_left[:3,:3] = y_rot_right @ p_left[:3,:3]
    p_left[0,3] -= t
    p_left[2,3] += 5

    return [p_top, p_bottom, p_left, p_right]

def build_pyr_point_cloud(pyr_pts, filename):
    """Builds a point cloud for a camera frustum visual.
    """
    num_pts = len(pyr_pts)
    element_vertex = 5*num_pts
    element_edge = 8*num_pts
    element_face = 6*num_pts

    with open(filename, 'w') as fh:
        # write header meta-data
        fh.write('ply\n')
        fh.write('format ascii 1.0\n')
        fh.write('comment Right-Handed System\n')
        fh.write('element vertex {}\n'.format(element_vertex))
        fh.write('property float x\n')
        fh.write('property float y\n')
        fh.write('property float z\n')
        fh.write('property uchar red\n')
        fh.write('property uchar green\n')
        fh.write('property uchar blue\n')
        
        # faces
        fh.write('element face {}\n'.format(element_face))
        fh.write('property list uchar int vertex_index\n')
        fh.write('end_header\n')

        # write vertex data to file
        for point in pyr_pts:
            pt = point[0]
            c = point[1]
            if c==2:
                color_center = np.asarray([80,80,80],dtype=np.ubyte)
                color_face = np.asarray([255,50,0],dtype=np.ubyte)
            elif c==1:
                color_center = np.asarray([80,80,80],dtype=np.ubyte)
                color_face = np.asarray([68,114,196],dtype=np.ubyte)


            fh.write(f'{pt[0,0,0]:.10f} {pt[0,1,0]:.10f} {pt[0,2,0]:.10f} {color_center[0]} {color_center[1]} {color_center[2]}\n')
            fh.write(f'{pt[1,0,0]:.10f} {pt[1,1,0]:.10f} {pt[1,2,0]:.10f} {color_face[0]} {color_face[1]} {color_face[2]}\n')
            fh.write(f'{pt[2,0,0]:.10f} {pt[2,1,0]:.10f} {pt[2,2,0]:.10f} {color_face[0]} {color_face[1]} {color_face[2]}\n')
            fh.write(f'{pt[3,0,0]:.10f} {pt[3,1,0]:.10f} {pt[3,2,0]:.10f} {color_face[0]} {color_face[1]} {color_face[2]}\n')
            fh.write(f'{pt[4,0,0]:.10f} {pt[4,1,0]:.10f} {pt[4,2,0]:.10f} {color_face[0]} {color_face[1]} {color_face[2]}\n')

        # write face data to file
        for i in range(num_pts):
            edge_ind = i*5
            fh.write(f'3 {edge_ind} {edge_ind+2} {edge_ind+3}\n')
            fh.write(f'3 {edge_ind} {edge_ind+1} {edge_ind+4}\n')
            fh.write(f'3 {edge_ind} {edge_ind+3} {edge_ind+4}\n')
            fh.write(f'3 {edge_ind} {edge_ind+1} {edge_ind+2}\n')
            fh.write(f'3 {edge_ind+1} {edge_ind+2} {edge_ind+4}\n')
            fh.write(f'3 {edge_ind+2} {edge_ind+3} {edge_ind+4}\n')
    return

def build_cam_pyr(cam_scale, fx, fy, cx, cy):
    """Constructs a camera frustum for visualization.
    """
    focallen   = fx * 0.4
    cam_w      = 2 * cx
    cam_h      = 2 * cy
    cam_center = np.array([0.0,          0.0,          0.0,      1.0])
    cam_ul     = np.array([cam_w * -0.5, cam_h * -0.5, focallen, 1.0])
    cam_ur     = np.array([cam_w *  0.5, cam_h * -0.5, focallen, 1.0])
    cam_dr     = np.array([cam_w *  0.5, cam_h *  0.5, focallen, 1.0])
    cam_dl     = np.array([cam_w * -0.5, cam_h *  0.5, focallen, 1.0])
    cam_top    = np.array([0.0,          cam_h * -0.7, focallen, 1.0])
    cam_center *= cam_scale
    cam_ul     *= cam_scale
    cam_ur     *= cam_scale
    cam_dr     *= cam_scale
    cam_dl     *= cam_scale
    cam_top    *= cam_scale
    cam_center[3] = 1.0
    cam_ul[3]     = 1.0
    cam_ur[3]     = 1.0
    cam_dr[3]     = 1.0
    cam_dl[3]     = 1.0
    cam_top[3]    = 1.0
    cam_center = cam_center.reshape((4, 1))
    cam_ul     = cam_ul.reshape((4, 1))
    cam_ur     = cam_ur.reshape((4, 1))
    cam_dr     = cam_dr.reshape((4, 1))
    cam_dl     = cam_dl.reshape((4, 1))
    cam_top    = cam_top.reshape((4, 1))
    return [cam_center, cam_ul, cam_ur, cam_dr, cam_dl, cam_top]

plot_cameras("/mnt/disk_1_ssd/luke/blub/traj_smpl_loss/aligned_poses_merged.txt", 0.00008, "/mnt/disk_1_ssd/luke/blub/traj_smpl_loss/aligned_poses_merged.ply")
plot_cameras("/mnt/disk_1_ssd/luke/blub/traj_smpl_loss/refined_poses_merged.txt", 0.00008, "/mnt/disk_1_ssd/luke/blub/traj_smpl_loss/refined_poses_merged.ply")
plot_cameras("/mnt/disk_1_ssd/luke/blub/traj_dual_loss/refined_poses_merged.txt", 0.00008, "/mnt/disk_1_ssd/luke/blub/traj_dual_loss/refined_poses_merged.ply")