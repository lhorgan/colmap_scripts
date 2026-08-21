= Dependencies
```
- pip install open3d
- pip install k-means-constrained
- pip install numpy
- pip install torch
- pip install opencv-python
- pip install pycolmap
```

= Running the pipeline
+ Run make_cave_spheres.py to make segmented image sequences.
+ Run make_fake_svins.py to make the fake svin files that will be used as pose priors.
+ Take the fake svins and combine them into one monolithtic svin file.
+ Run make_db.sh to create the database and populate it with pose priors and features.
+ Run lights.py to run colmap on the segmented image sequences. This will create a sparse reconstruction for each sequence.
+ Run ```python make_text_models.py <path_to_spheres>```
 - ie ```python make_text_models.py /mnt/disk_1_ssd/luke/blub/spheres```
+ Run make_overlap_graph.py to create a graph of the overlap between the sparse reconstructions. This will be used to find pairs of sequences that have enough overlap to be merged.
+ Run make_svins.py to create svin files for each model, one by filtering the real SVIn file, and one from COLMAP. These will be used as input to the coarse alignment step.
 - You will need to combine the *real* svin files into one monolithic svin file, and update the path in tree3.py to point to it.
+ Run tree3.py to do a coarse alignment using the camera trajectories.
+ Run sweeplign3.py to optimize the alignment.
+ Run crayons.py to produce true color versions of the aligned point clouds.
+ Run get_aligned_cams.py to apply the refined transformations from sweeplign3.py to the camera poses.
+ Run plot_cams.py to visualize the camera poses, if you want.
