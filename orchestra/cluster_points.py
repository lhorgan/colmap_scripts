# The code is in this file is mostly by Claude, following directions
# provided by the authors.
# https://claude.ai/chat/c689e09f-7623-42d1-833a-d224906bda86

from __future__ import annotations

import numpy as np
from k_means_constrained import KMeansConstrained


def cluster_points(
    points: list[tuple[float, float, float]],
    num_clusters: int,
    expansion: float = 0.20
) -> tuple[list[list[int]], np.ndarray]:
    """
    Cluster 3D points into roughly equal-sized groups with overlapping membership.
    
    Args:
        points: List of (x, y, z) tuples
        num_clusters: Number of clusters to create
        expansion: Fraction of cluster size - each cluster will also include
                   this proportion of nearest external points (default 0.20 = 20%)
    
    Returns:
        cluster_memberships: For each point (by index), a list of cluster indices it belongs to
        centers: Array of cluster centroids, shape (num_clusters, 3)
    """
    X = np.array(points)
    n_points = len(X)
    
    # Calculate size constraints for balanced clusters
    base_size = n_points // num_clusters
    remainder = n_points % num_clusters
    size_min = base_size
    size_max = base_size + (1 if remainder > 0 else 0) + 1
    
    # Run constrained k-means
    clf = KMeansConstrained(
        n_clusters=num_clusters,
        size_min=size_min,
        size_max=size_max,
        random_state=42
    )
    clf.fit(X)
    
    labels = clf.labels_
    centers = clf.cluster_centers_
    
    # Initialize memberships with original assignments
    cluster_memberships = [[labels[i]] for i in range(n_points)]
    original_memberships = [labels[i] for i in range(n_points)]
    
    # For each cluster, add the n closest external points
    for cluster_idx in range(num_clusters):
        mask = (labels == cluster_idx)
        cluster_size = np.sum(mask)
        n_to_add = max(1, int(cluster_size * expansion))
        
        # Get indices of external points
        external_indices = np.where(~mask)[0]
        
        # Calculate distances from this cluster's center to external points
        external_distances = np.linalg.norm(X[external_indices] - centers[cluster_idx], axis=1)
        
        # Find the n closest external points
        closest_indices = external_indices[np.argsort(external_distances)[:n_to_add]]
        
        # Add this cluster to their memberships
        for idx in closest_indices:
            cluster_memberships[idx].append(cluster_idx)
    
    # Debug: print final cluster sizes
    print("Final cluster sizes:")
    for cluster_idx in range(num_clusters):
        size = sum(1 for m in cluster_memberships if cluster_idx in m)
        print(f"  Cluster {cluster_idx}: {size} points")
    
    return cluster_memberships, centers, original_memberships


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)
    
    # Simulate a camera trajectory (winding path)
    t = np.linspace(0, 4 * np.pi, 200)
    trajectory_points = [
        (10 * np.cos(t_i), 10 * np.sin(t_i), t_i)
        for t_i in t
    ]
    
    memberships, centers, = cluster_points(
        points=trajectory_points,
        num_clusters=8,
        expansion=0.20
    )
    
    print(f"Points: {len(trajectory_points)}")
    print(f"Clusters: {len(centers)}")
    
    multi = sum(1 for m in memberships if len(m) > 1)
    print(f"Points in multiple clusters: {multi}")