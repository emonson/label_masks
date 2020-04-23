# if using Anaconda Python (3), Numpy and json should be installed by default
# but you can install scikit-image with

# conda install scikit-image

# or create a new environment for doing this work with ("mask" is an arbitrary name)

# conda create --name mask scikit-image
# conda activate mask

from skimage import draw, io
import numpy as np
import json
import os

# '.' is the current directory. Replace this with the directory where the
# JSON files and images live
json_dir = '.'
json_file_name = 'export-2020-04-17T19_22_10.412Z.json'
image_dir = '.'


# Got this function from
# https://github.com/scikit-image/scikit-image/issues/1103#issuecomment-52378754
# (modified slightly to change from boolean mask array to 8-bit unsigned int)

def poly2mask(vertex_row_coords, vertex_col_coords, shape):
    fill_row_coords, fill_col_coords = draw.polygon(vertex_row_coords, vertex_col_coords, shape)
    # In 8-bit alpha channel, 0 = invisible, 255 = completely visible
    mask = np.zeros(shape, dtype=np.uint8)
    mask[fill_row_coords, fill_col_coords] = 255
    return mask

with open(os.path.join(json_dir, json_file_name),'r') as f:
    annotations = json.load(f)

for ann in annotations:

    # Right now only looking for polygon objects – skipping pixel-based labels
    # so build up a list of features that have poly objects
    objects = ann['Label']['objects']
    poly_objects = []
    for ob in objects:
        if 'polygon' in ob:
            # Make a couple of convenience arrays that poly2mask() wants
            # instead of the {'x':num, 'y':num} format the coordinates are in the JSON
            poly_x = np.array([dd['x'] for dd in ob['polygon']])
            poly_y = np.array([dd['y'] for dd in ob['polygon']])
            poly_objects.append({'featureId':ob['featureId'],
                                  'polygon':ob['polygon'],
                                  'poly_x':poly_x, 'poly_y':poly_y})

    # Only bother loading in the annotated image if it has polygon features
    if len(poly_objects) > 0:
        img_file_name = ann['External ID']
        print("File:", img_file_name)
        img = io.imread(os.path.join(image_dir, img_file_name))

        for poly in poly_objects:
            print('\t', "feature:", poly['featureId'])
            # In Numpy array, x = image width direction, y = image height direction
            ww = poly['poly_x']
            hh = poly['poly_y']
            # height = row coords, width = column coords
            mask = poly2mask(hh, ww, img.shape[:2])
            # Create a new array, now with an alpha channel: 4-dim (r,g,b,a)
            img_a = np.zeros((img.shape[0], img.shape[1], 4), dtype=np.uint8)
            img_a[:,:,0:3] = img
            img_a[:,:,3] = mask
            # Slice objects allow us to use variables for bounds of array slices
            # NOTE: may need to adjust use of .round() here if rounding is not giving the
            #   proper crop! Could also subtract or add padding. 
            crop_w = slice(ww.min().round().astype('int'), ww.max().round().astype('int'))
            crop_h = slice(hh.min().round().astype('int'), hh.max().round().astype('int'))
            # NOTE: Should add try-catch for IndexError here, or bounds check before crop!!
            img_a_cropped = img_a[crop_h,crop_w,:]

            old_name_nodots = img_file_name.replace('.','_')
            img_outpath = os.path.join(image_dir, old_name_nodots +'_'+ poly['featureId'] +'.png')
            io.imsave(img_outpath, img_a_cropped)
