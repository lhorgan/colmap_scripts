from __future__ import annotations

# https://claude.ai/chat/c689e09f-7623-42d1-833a-d224906bda86

import numpy as np
from k_means_constrained import KMeansConstrained

def cluster_points(
    points: list[tuple[float, float, float]],
    num_clusters: int,
    expansion: float = 0.20
) -> tuple[list[list[int]], np.ndarray, np.ndarray]:
    """
    Cluster 3D points into roughly equal-sized groups with overlapping spheres.
    
    Args:
        points: List of (x, y, z) tuples
        num_clusters: Number of clusters to create
        expansion: Fraction to expand each cluster radius (default 0.20 = 20%)
    
    Returns:
        cluster_memberships: For each point (by index), a list of cluster indices it belongs to
        centers: Array of cluster centroids, shape (num_clusters, 3)
        expanded_radii: Array of expanded radii for each cluster
    """
    X = np.array(points)
    n_points = len(X)
    
    # Calculate size constraints for balanced clusters
    base_size = n_points // num_clusters
    remainder = n_points % num_clusters
    
    # Allow some flexibility: min is floor, max is ceil
    size_min = base_size
    size_max = base_size + (1 if remainder > 0 else 0) + 1  # +1 for flexibility
    
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
    
    # Calculate radius for each cluster (max distance from centroid)
    radii = np.zeros(num_clusters)
    for i in range(num_clusters):
        mask = (labels == i)
        cluster_points = X[mask]
        distances = np.linalg.norm(cluster_points - centers[i], axis=1)
        radii[i] = distances.max()
    
    # Expand radii
    expanded_radii = radii * (1 + expansion)
    
    # Determine cluster membership for each point (with overlap)
    cluster_memberships = []
    for point in X:
        memberships = []
        for cluster_idx in range(num_clusters):
            distance = np.linalg.norm(point - centers[cluster_idx])
            if distance <= expanded_radii[cluster_idx]:
                memberships.append(cluster_idx)
        cluster_memberships.append(memberships)
    
    return cluster_memberships, centers, expanded_radii


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)
    
    # Generate some test points
    test_points = [
        tuple(p) for p in np.random.randn(100, 3) * 10
    ]
    
    memberships, centers, radii = cluster_points(
        points=test_points,
        num_clusters=5,
        expansion=0
    )
    
    print(f"Number of points: {len(test_points)}")
    print(f"Number of clusters: {len(centers)}")
    print(f"\nCluster centers:\n{centers}")
    print(f"\nExpanded radii: {radii}")
    
    # Count how many points belong to multiple clusters (overlap)
    multi_cluster = sum(1 for m in memberships if len(m) > 1)
    print(f"\nPoints belonging to multiple clusters: {multi_cluster}")
    
    # Show first 10 point memberships
    print(f"\nFirst 10 point memberships:")
    for i, m in enumerate(memberships[:10]):
        print(f"  Point {i}: clusters {m}")