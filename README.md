# Cropped labeled image regions with alpha mask

Starting with image label regions defined by polygons or bitmaps, create alpha mask
with invisible pixels outside labeled region, and save cropped feature PNG image.
Scripts have been developed for both Labelbox and Supervisely.

## Dependencies

My recommendation would be to start with the
[Anaconda Python 3](https://www.anaconda.com/distribution/#download-section)
distribution. This is just normal Python, but you can install it for just "yourself"
without any administrator privileges and it'll all end up in a directory within your
user folder.

The Labelbox script only needs 
[scikit-image](https://scikit-image.org/), 
beyond what's installed by default in the standard Anaconda distribution, 
but the Supervisely script additionally requires 
[opencv](https://anaconda.org/anaconda/opencv), 
[PIL](https://anaconda.org/anaconda/pillow), and
[zlib](https://anaconda.org/anaconda/zlib).

I would recommend creating a new environment for doing this work with 
("mask" is an arbitrary name):

```
conda create --name mask opencv pillow scikit-image numpy zlib
```

and then activate that environment with

```
conda activate mask
```

## Running the code

*Note that I've included a sample of the data directories and output that I describe
below, but not the entire output of running the scripts. The Jupyter notebooks
are just sandbox test code where I worked out the code for the real scripts.*

### Labelbox

The Labelbox script only requires the JSON export. It will download everything else
from the Labelbox servers. It expects the JSON to be placed in a data directory that
you create, the name of which you need to edit in the beginning of the script. 
It will save all of the images and an error log within that directory and subdirectories.
The script itself should be in the same directory as the data directory (not within
the data directory).

```
python Labelbox_masks.py
```

### Supervisely

The Supervisely script relies on the workspace export you get by 
`Download as -> .json + images`. That archive (.tar file) should be expanded, and
the folder created should sit in the same directory as the script. You then need to 
edit the main data directory name in the script to match the project name 
before running.

```
python Supervisely_masks.py
```

### Labelbox Containers

Supervisely has the concept of container objects, but Labelbox doesn't have that
built in. This script runs through the Labelbox JSON export, and for each image
gathers the objects with a title that has "container" in them. Then, it compares
each feature object to the containers to see whether it overlaps completely with one
of them. If it does, the `featureId` of the parent container object is recorded
in the `instance` field of the feature.

The code is complicated slightly so it will run faster: Before testing whether the 
pixels of two objects overlap, it first tests to see if their bounding boxes overlap,
because this is a *much* faster test, and can quickly exclude bad container candidates.

Before running, you should edit the name of the JSON file, and the name of the output
JSON file. **Dont' write over the original!**

```
python Labelbox_Containers.py
```

