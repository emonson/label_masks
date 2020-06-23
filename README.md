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

### Labelbox

The Labelbox script only requires the JSON export. It will download everything else
from the Labelbox servers. It expects the JSON to be placed in a data directory that
you create, the name of which you need to edit in the beginning of the script. 
It will save all of the images and an error log within that directory and subdirectories.
The script itself should be in the same directory as the data directory (not within
the data directory).

```
python Supervisely_masks.py
```

### Supervisely

The Supervisely script relies on the workspace export you get by 
`Download as -> .json + images`. That archive (.tar file) should be expanded, and
the folder created should sit in the same directory as the script. I don't think you
should have to edit the paths beyond this unless you don't like the default folder names.

```
python Supervisely_masks.py
```