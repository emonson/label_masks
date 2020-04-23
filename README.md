# skimage-polymask

Starting with image label regions defined by polygons, create alpha mask
with invisible pixels outside polygon, and save cropped feature PNG image.

## Dependencies

If you're using using 
[Anaconda Python 3](https://www.anaconda.com/distribution/#download-section), 
`Numpy` and `json` modules should be installed by default
but you can install scikit-image with

```
conda install scikit-image
```

or create a new environment for doing this work with ("mask" is an arbitrary name)

```
conda create --name mask scikit-image
```

and then activate that environment with

```
conda activate mask
```

## Running the code

Right now the main script, `poly_mask_crop.py` is written to load in a specific
JSON file and expects both the JSON and images to be in the same directory as the script.
Modify the beginning of the file to set the JSON file name, plus the directory for
the images and JSON.

In the Anaconda Prompt (Windows) or Terminal (Mac) change to the directory
where the code is and type:

```
python poly_mask_crop.py
```