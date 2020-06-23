#!/usr/bin/env python
# coding: utf-8

# `PIL` is really installed as `pillow`
# `cv2` is really installed as `opencv`

# To create a new conda environment with requirements called cv2 (name doesn't matter)
# conda create --name cv2 opencv pillow scikit-image numpy zlib

from skimage import draw
from skimage import io as skio
import numpy as np
import json
import os
import glob

import cv2
from PIL import Image
import zlib
import io
import base64


data_dir = os.path.join('.','Book of Fortresses','Book of Fortresses')
ann_dir = os.path.join(data_dir,'ann')
img_dir = os.path.join(data_dir,'img')
mask_dir = os.path.join(data_dir,'masked_features')

# Grabbed poly2mask function from:
# https://github.com/scikit-image/scikit-image/issues/1103#issuecomment-52378754

def poly2mask(vertex_row_coords, vertex_col_coords, shape):
    fill_row_coords, fill_col_coords = draw.polygon(vertex_row_coords, vertex_col_coords, shape)
    mask = np.zeros(shape, dtype=np.uint8)
    mask[fill_row_coords, fill_col_coords] = 255
    return mask

# https://docs.supervise.ly/data-organization/import-export/supervisely-format#bitmap
# Heeded a warning and changed `np.fromstring()` to `np.frombuffer()` and seems to work fine

def base64_2_mask(s):
    z = zlib.decompress(base64.b64decode(s))
    n = np.frombuffer(z, np.uint8)
    mask = cv2.imdecode(n, cv2.IMREAD_UNCHANGED)[:, :, 3]
    return mask

# Not using this one here, but including it for reference
def mask_2_base64(mask):
    img_pil = Image.fromarray(np.array(mask, dtype=np.uint8))
    img_pil.putpalette([0,0,0,255,255,255])
    bytes_io = io.BytesIO()
    img_pil.save(bytes_io, format='PNG', transparency=0, optimize=0)
    bytes = bytes_io.getvalue()
    return base64.b64encode(zlib.compress(bytes)).decode('utf-8')


try: 
    os.mkdir(mask_dir)
except OSError:
    if not os.path.exists(mask_dir):
        sys.exit("Error creating: " + mask_dir)

ann_list = glob.glob(os.path.join(ann_dir,'*.json'))

for ann_path in ann_list:
    
    print(ann_path)
    
    # remove .json extension – should maybe use pathlib instead...
    img_filename = os.path.splitext(os.path.basename(ann_path))[0]
    # replace . with _ for mask subdirectory name
    mask_subdir = img_filename.replace('.','_')
    mask_subdir_path = os.path.join(mask_dir, mask_subdir)
    # remove .jpg extension
    img_name = os.path.splitext(img_filename)[0]
    img_path = os.path.join(img_dir, img_filename)
    
    img = skio.imread(img_path)

    try: 
        os.mkdir(mask_subdir_path)
    except OSError:
        if not os.path.exists(mask_subdir_path):
            sys.exit("Error creating: " + mask_subdir_path)

    with open(ann_path,'r') as f:
        annotations = json.load(f)

    # --- Objects loop
    
    for ii,ob in enumerate(annotations['objects']):
        
        geometry_type = ob['geometryType']
        print(ii, ob['id'], geometry_type)
        
        # --- Polygon
        
        if geometry_type == 'polygon':
            
            n_interior = len(ob['points']['interior'])
            if n_interior > 0:
                print('\t Interior points! n =', n_interior)
            
            # NOTE: Just exterior points for now...
            #   If doing polygon regions with holes, need to create that shape logic code
            points = ob['points']
            exterior = np.array(points['exterior'])

            # Do the crop before creating masked image
            # To get all the way cropped should really add 1 to rmin. Not sure why...

            [cmin,rmin] = exterior.min(axis=0)
            [cmax,rmax] = exterior.max(axis=0)
            exterior_offset = exterior - exterior.min(axis=0)
            ww = exterior_offset[:,0]
            hh = exterior_offset[:,1]
            
            img_masked = np.zeros((rmax-rmin,cmax-cmin,4), dtype=np.uint8)
            mask = poly2mask(hh, ww, img_masked.shape[:2])
            
            img_masked[:,:,:3] = img[slice(rmin,rmax), slice(cmin,cmax), :3]
            img_masked[:,:,3] = mask

        # --- Bitmap

        elif geometry_type == 'bitmap':
        
            bitmap = ob['bitmap']
            mask = base64_2_mask(bitmap['data'])
            rr,cc = mask.shape
            cc0,rr0 = bitmap['origin']

            img_masked = np.zeros((rr,cc,4), dtype=np.uint8)

            img_masked[:,:,:3] = img[slice(rr0,rr0+rr), slice(cc0,cc0+cc), :3]
            img_masked[:,:,3] = mask        
        
        # --- Not handling anything beyond Polygon or Bitmap for now
        
        else:
            continue

        # Save masked image file
        img_masked_name = img_name+'_'+str(ob['classId'])+'_'+str(ob['id'])+'.png'
        skio.imsave(os.path.join(mask_subdir_path,img_masked_name), img_masked)
