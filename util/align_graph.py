import os

from refine import align_point_clouds_icp, read_point_cloud, write_point_cloud, get_transform_icp
import numpy as np

def filter(root):
    entries = os.listdir(root)
    for entry in entries:
        entry = entry[:-4]
        entry = entry.split("_")
        src = int(entry[0])
        dst = int(entry[-1])

        src_to_dst = read_point_cloud(f"{root}/{src}_close_to_{dst}.ply")
        dst_to_src = read_point_cloud(f"{root}/{dst}_close_to_{src}.ply")

        if len(dst_to_src.points) > 3000 and len(src_to_dst.points) > 3000:
            write_point_cloud(src_to_dst, f"/home/luke/xmas/NeighborsFiltered/{src}_close_to_{dst}.ply")
            write_point_cloud(dst_to_src, f"/home/luke/xmas/NeighborsFiltered/{dst}_close_to_{src}.ply")

def make_graph(root):
    entries = os.listdir(root)

    graph = {}

    for entry in entries:
        entry = entry[:-4]
        entry = entry.split("_")
        src = int(entry[0])
        dst = int(entry[-1])

        if src not in graph:
            graph[src] = set()
        graph[src].add(dst)

    return graph

def bfs(graph, start_node):
    queue = [start_node]
    visted = set([start_node])
    parents = {start_node: None}

    bfs_path = []

    while len(queue) > 0:
        node = queue.pop(0)
        bfs_path.append(node)
        print(f"At {node} from {parents[node]}")
        neighbors = graph[node]
        for neighbor in neighbors:
            if neighbor not in visted:
                visted.add(neighbor)
                queue.append(neighbor)
                parents[neighbor] = node
    
    return parents, bfs_path

def get_pcd_name(node1, node2):
    return f"{node1}_close_to_{node2}.ply"

def get_transforms(parents, path, subroot):
    transforms = {}

    for node in path:
        parent = parents[node]
        if parent is None:
            transforms[node] = np.eye(4)
            continue

        parent_pcd = read_point_cloud(f"{subroot}/{parent}_close_to_{node}.ply")
        node_pcd = read_point_cloud(f"{subroot}/{node}_close_to_{parent}.ply")

        print(f"Transform from {node} to {parent}")
        parent_transform = transforms[parent]
        transform_to_parent = get_transform_icp(parent_pcd, node_pcd) # Align node to parent
        transforms[node] = parent_transform @ transform_to_parent
        print(transforms[node])
    
    return transforms

def do_transforms(transforms, fullroot, dstroot):
    for node in transforms:
        transform = transforms[node]
        pcd = read_point_cloud(f"{fullroot}/bin_{node}.ply")
        aligned = pcd.transform(transform)
        write_point_cloud(aligned, f"{dstroot}/bin_{node}.ply")
    

def main():
    subroot = "/home/luke/xmas/NeighborsFiltered"
    fullroot = "/home/luke/xmas/AlignedCubes"
    dstroot = "/home/luke/xmas/refined1"
    graph = make_graph(subroot)
    parents, path = bfs(graph, start_node=0)
    print(len(path))
    transforms = get_transforms(parents, path, subroot)
    do_transforms(transforms, fullroot, dstroot)

    #filter(subroot)

    # parent = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_0.ply")
    # node = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_1.ply")
    # transform = get_transform_icp(parent, node)
    # aligned = node.transform(transform)
    # write_point_cloud(aligned, "/home/luke/xmas/wtf.ply")





if __name__ == "__main__":
    main()