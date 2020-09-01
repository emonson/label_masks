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

json_file = 'export-2020-07-23T01_23_49.887Z.json'
data_dir = os.path.join('.','LabelboxMasks')

json_path = os.path.join(data_dir,json_file)
image_dir = os.path.join(data_dir,'images')
mask_dir = os.path.join(data_dir,'masks')
masked_feature_dir = os.path.join(data_dir,'masked_features')
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

for ann in annotations:

    # ### Check for saved image, then download and save if doesn't exist
    image_filename = ann['External ID']
    # This will be used as a subdirectory for masks and features
    img_subdir = image_filename.replace('.','_')
    print(image_filename)
    image_path = os.path.join(image_dir, image_filename)

    if os.path.exists(image_path):
        print('Reading from pre-saved file')
        img = io.imread(image_path)
    else:
        print('Reading from URI and saving JPG')
        img = io.imread(ann['Labeled Data'])
        io.imsave(image_path, img)

    # ### Read first from downloaded mask files, then URI
    for obj in ann['Label']['objects']:
        mask_id = obj['featureId']
        # This ID gives HTTP error, which slows down progress – skipping
        if mask_id in ['ckb16dq3w00l80ya3b9b7bn7z'] : continue
        print('\t',mask_id)
        mask_dest_dir = os.path.join(mask_dir, img_subdir)
        mask_path = os.path.join(mask_dest_dir, mask_id+'.png')
        
        try: 
            os.mkdir(mask_dest_dir)
        except OSError:
            if not os.path.exists(mask_dest_dir):
                sys.exit("Error creating: " + mask_dest_dir)

        masked_img_dest_dir = os.path.join(masked_feature_dir, img_subdir)
        masked_img_path = os.path.join(masked_img_dest_dir, mask_id+'.png')

        try: 
            os.mkdir(masked_img_dest_dir)
        except OSError:
            if not os.path.exists(masked_img_dest_dir):
                sys.exit("Error creating: " + masked_img_dest_dir)

        if os.path.exists(mask_path):
            if os.path.exists(masked_img_path):
                print('\t Already done', mask_path)
                continue
            else:
                print('\t Reading mask image from file')
                mask_img = io.imread(mask_path)
        else:
            print('\t * Downloading mask image from server')
            # Delay just so we don't get kicked off of the server...
            time.sleep(1+1*random.random())
            try:
                mask_img = io.imread(obj['instanceURI'])
            except HTTPError as err:
                with open(log_path,'a') as f:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(now+" "+image_filename+" "+mask_id+" "+str(err.status)+" "+str(err.reason)+"\n")
                print(err.status,err.reason,mask_id)
                continue
            # Getting a UserWarning about low-contrast image being saved: ignore
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                io.imsave(mask_path, mask_img)

        # Create cropped, alpha-masked image feature
        (rmin,rmax),(cmin,cmax) = bbox2(mask_img[:,:,3])
        if (rmax-rmin)<=1:
            with open('masks_errors.log','a') as f:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(now+" "+image_filename+" "+mask_id+" Blank mask!!\n")
        img_masked = np.zeros((rmax-rmin,cmax-cmin,4), dtype=np.uint8)
        img_masked[:,:,:3] = img[slice(rmin,rmax), slice(cmin,cmax), :3]
        img_masked[:,:,3] = mask_img[slice(rmin,rmax), slice(cmin,cmax), 3]
      
        # Save masked image feature as PNG
        print('\t','\t','Saving masked feature PNG')
        io.imsave(masked_img_path, img_masked)
