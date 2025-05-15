I still need to consoldiate everything so it exists as one pipeline.  For now, different tasks require different scripts and different setups.

# Incremental Model Refiner
The incremental model refiner is Torsten's new addition which actually allows us to initialize with honest to goodness pose priors.  To use it, you need to check out Torsten's fork of Colmap.

https://github.com/tsattler/colmap.git

Then, you need to switch to the branch "patch-5" and follow the normal Colmap installation instructions (https://colmap.github.io/install.html).

Alright, let's get started.

Create your data path directory.  Inside of it, create a sub-directory for the scene.  It should contain an "Images" folder with all of your images.  It should also contain a file called "svin.txt" with the relevant camera poses.

- <data_path>/
  - <scene_name>/
    - svin.txt
    - Images/

The incremental model refiner expects *camera centers*, not offsets.  See SVIN Business for more information.  Do not use the original SVIN file.  Use the version with camera centers!

__All scripts referenced for the rest of this section are in the *colmap_with_known_poses* subdirectory.__

Open run_423.sh.  Change the DATA_PATH variable on the first line to match your <data_path>.  Change the SCENE variable on the second line to match your <scene_name>.

You're doing great.

Now, just run run_423.sh.

```bash
./run_423.sh
```

Or, better yet, create a log file at /path/to/log/file/log.txt, and then run:

```bash
./run_423.sh > /path/to/log/file/log.txt 2>&1
```

(If you want to be extra safe about it, I highly recommend using screen!)

Once that's done, you'll have a sparse model.

Now, let's do dense.  It's very easy.  Open run_dense.sh and change the DATA_PATH and SCENE variables exactly the same way as before.  Then:

```
./run_dense.sh > /path/to/log/file/log.txt 2>&1
```

Et voilà!  It's only perhaps 96 hours later, and you're done!

# Everything Else
__All scripts referenced for the rest of this section are in the *clean* subdirectory.__

Start by creating your data path directory.   Inside of it, create a sub-directory for the scene.  It should contain an "Images" folder with all of your images.

- <data_path>/
  - <scene_name>/
    - Images/

If all of your images are from one camera, then the Images directory should simply contain the images directly.  The pipeline also supports a three-camera setup.  Generic support for more cameras could be easily added in the future.  If you have three cameras, place your images inside Left/Center/Right subdirectories.

- <data_path>/
  - <scene_name>/
    - Images/
      - Left/
      - Center/
      - Right/

### Pose Prior Mapper
The pose prior mapper is probably misnamed.  We think it probably does bundle adjustment like the normal mapper, without taking the pose priors into account, and then computes a single transformation to line up with the "priors" afterwards.  Oh well.

Unlike the Incremental Model Refiner, the pose prior mapper does *not* expect camera centers.  The pipeline accepts raw SVIN poses and puts them into COLMAP's database in the appropriate format.  

Note that the Pose Prior Mapper  only supports the three camera setup.  It would be easy enough to make it support one camera, but such is the nature of the brittle scripts I have put together thus far!

Add the SVIN files to your data directory inside a folder called SVIN, with one txt file for each camera.  These files must have the same names as their corresponding image folders.

- <data_path>/
  - <scene_name>/
    - Images/
      - Left/
      - Center/
      - Right/
    - SVIN/
      - Left.txt
      - Center.txt
      - Right.txt

Open run_with_poses.sh and change the first two lines to match your data path and scene.  Then run:

```
./run_with_poses.sh
```

### GLOMAP
GLOMAP does not support initialization with poses, but it is very fast!  Create your data path and scene as in the other examples.

If you have one camera:

- <data_path>/
  - <scene_name>/
    - Images/

And if you have three:

- <data_path>/
  - <scene_name>/
    - Images/
      - Left/
      - Center/
      - Right/

Then, simply execute:

```
./run.sh
```

# SVIN BUSINESS
### Camera Centers
To obtain camera centers from a standard SVIN txt file, just use the handy invert_svin.py script.  Open invert_svin.py and change the arguments to the invert function to be the paths to

1) your original SVIN file
2) the destination of the converted SVIN file

Then run
```
python invert_svin.py
```

### Filtering out unused poses
If you want to make sure your SVIN file only has poses for images that actually exist in your Images directory, use the filter_svin.py script.  Open filter_svin.py and change the arguments to the filter_svin function on the last line to suit your configuration.  The arguments are:

1) The path to your original SVIN file
2) The path where you'd like a revised SVIN file to be written
3) The path to the folder of images you'd like the SVIN file to match