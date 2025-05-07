I still need to consoldiate everything so it exists as one pipeline.  For now, different tasks require different scripts and different setups.

---

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

__All scripts referenced for the rest of this section are in the colmap_with_known_poses subdirectory.__

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