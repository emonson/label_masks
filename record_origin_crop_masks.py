#!/usr/bin/env python
# coding: utf-8

from skimage import draw, io
# from skimage.measure import approximate_polygon, find_contours
import numpy as np
import json
import os
import warnings
import time
from datetime import datetime
import random
from urllib.error import HTTPError

json_file = 'export-2020-07-23T01_23_49.887Z_instanceFixed.json'
output_json_file = 'export-2020-07-23T01_23_49.887Z_instanceFixedOrigin.json'
data_dir = os.path.join('.','LabelboxMasks')

json_path = os.path.join(data_dir,json_file)
mask_dir = os.path.join(data_dir,'masks')
cropped_mask_dir = os.path.join(data_dir,'cropped_masks')
log_path = os.path.join(data_dir,'masks_errors.log')

# ### JSON Schema
# 
# - **annotations** : JSON list of objects, one per labeled image (book page)
# - **External ID** : name of the image
# - **Labeled Data** : URI of the image
# - **Label** : Object containing all labels
#     - **objects** : List of all labeled feature objects
#         - **featureId** : unique ID for the feature *(used in the URI, and I'll use for a file name)*
#         - **instanceURI** : URI of the mask image *(exists for both polygons and bitmaps)*
#         - **polygon** : list of x,y objects containing the coordinates of the polygon vertices *(won't exist for a pure bitmap mask)*
#         

# ### Finding mask bounds
#
# If we find the mask bounding box we can use it to crop everything and never created a full-sized masked image. 
# Tested this np.any() method against np.argwhere() method, and it is indeed much faster
# https://stackoverflow.com/questions/4808221/is-there-a-bounding-box-function-slice-with-non-zero-values-for-a-ndarray-in
# 
# %timeit bbox2(mask00[:,:,3])
# 26.7 ms ± 350 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

def bbox2(img):
    rows = np.any(img, axis=1)
    cols = np.any(img, axis=0)
    try:
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
    except IndexError:
        # NOTE: Not sure this is the right decision on what to return for blank mask
        rmin, rmax = (0,0)
        cmin, cmax = (0,0) 
    return (rmin,rmax+1), (cmin,cmax+1)

# Load JSON
with open(json_path,'r') as f:
    annotations = json.load(f)

for ann_idx, ann in enumerate(annotations):

    image_filename = ann['External ID']
    # This will be used as a subdirectory for masks and features
    img_subdir = image_filename.replace('.','_')
    print(image_filename)

    # Make sure the cropped mask directory exists
    try: 
        os.mkdir(cropped_mask_dir)
    except OSError:
        if not os.path.exists(cropped_mask_dir):
            sys.exit("Error creating: " + cropped_mask_dir)

    # Loop through all objects
    # Keep track of obj index, so can insert instance ID in proper place
    for obj_idx, obj in enumerate(ann['Label']['objects']):
        mask_id = obj['featureId']
        # This ID gives HTTP error, which slows down progress – skipping
        if mask_id in ['ckb16dq3w00l80ya3b9b7bn7z'] : continue
        print('\t',mask_id)
        mask_dest_dir = os.path.join(mask_dir, img_subdir)
        mask_path = os.path.join(mask_dest_dir, mask_id+'.png')
        
        cropped_mask_dest_dir = os.path.join(cropped_mask_dir, img_subdir)
        cropped_mask_path = os.path.join(cropped_mask_dest_dir, mask_id+'.png')

        # Make sure the cropped mask + img_subdir directory exists
        try: 
            os.mkdir(cropped_mask_dest_dir)
        except OSError:
            if not os.path.exists(cropped_mask_dest_dir):
                sys.exit("Error creating: " + cropped_mask_dest_dir)

        # Read the mask (just let it error out for now if not there...)
        mask_img = io.imread(mask_path)

        # Create cropped, alpha-mask
        (rmin,rmax),(cmin,cmax) = bbox2(mask_img[:,:,3])
        if (rmax-rmin)<=1:
            with open(log_path,'a') as f:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(now+" "+image_filename+" "+mask_id+" Blank mask!!\n")

        # Copying mask image into four channels of RGBA so it'll end up with the proper
        # alpha channel, but also have white inside of masked area
        # https://stackoverflow.com/questions/32171917/copy-2d-array-into-3rd-dimension-n-times-python
        # This is the same thing as creating an empty 4-channel image array and copying
        #   the uint8 mask array of all 255s into all four channels separately, but wanted to know how
        #   to do this in a fancy Numpy way with np.broadcast_to()
        # Note: if xx.shape == (3,2), xx[...,None].shape == (3,2,1)
        #   and (3,2)+(4,) == (3,2,4)
        mask_cropped = mask_img[slice(rmin,rmax), slice(cmin,cmax), 3]
        mask_cropped_white = np.broadcast_to(mask_cropped[...,None], mask_cropped.shape+(4,))        
        
        # Record mask origin in JSON
        annotations[ann_idx]['Label']['objects'][obj_idx]['origin'] = [rmin,cmin]
        
        # Save cropped mask as PNG
        io.imsave(cropped_mask_path, mask_cropped_white)

# Write out new JSON file
with open(os.path.join(data_dir, output_json_file), 'w', encoding='utf-8') as f:
    json.dump(annotations, f, ensure_ascii=False, indent=4)
