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


data_dir = os.path.join('.','Goa')
ann_dir = os.path.join(data_dir,'ann')
img_dir = os.path.join(data_dir,'img')
mask_dir = os.path.join(data_dir,'masks')
masked_feature_dir = os.path.join(data_dir,'masked_features')

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

# supervisely/plugins/dtl/legacy_supervisely_lib/figure/figure_line.py
# shape_hw = bitmap.shape[:2]
def to_uint8_mask(exterior, interiors, shape_hw):
    bmp_to_draw = np.zeros(shape_hw, np.uint8)
    cv2.fillPoly(bmp_to_draw, pts=[exterior], color=255)
    cv2.fillPoly(bmp_to_draw, pts=interiors, color=0)
    to_contours = [interior[:, np.newaxis, :] for interior in interiors]
    cv2.drawContours(bmp_to_draw, to_contours, contourIdx=-1, color=255)
    return bmp_to_draw

try: 
    os.mkdir(mask_dir)
except OSError:
    if not os.path.exists(mask_dir):
        sys.exit("Error creating: " + mask_dir)

try: 
    os.mkdir(masked_feature_dir)
except OSError:
    if not os.path.exists(masked_feature_dir):
        sys.exit("Error creating: " + masked_feature_dir)

ann_list = glob.glob(os.path.join(ann_dir,'*.json'))

for ann_path in ann_list:
    
    print(ann_path)
    
    # remove .json extension – should maybe use pathlib instead...
    img_filename = os.path.splitext(os.path.basename(ann_path))[0]
    # replace . with _ for mask subdirectory name
    img_name_subdir = img_filename.replace('.','_')
    mask_path = os.path.join(mask_dir, img_name_subdir)
    masked_feature_path = os.path.join(masked_feature_dir, img_name_subdir)
    # remove .jpg extension
    img_name = os.path.splitext(img_filename)[0]
    img_path = os.path.join(img_dir, img_filename)
    
    img = skio.imread(img_path)

    try: 
        os.mkdir(mask_path)
    except OSError:
        if not os.path.exists(mask_path):
            sys.exit("Error creating: " + mask_path)

    try: 
        os.mkdir(masked_feature_path)
    except OSError:
        if not os.path.exists(masked_feature_path):
            sys.exit("Error creating: " + masked_feature_path)

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
            exterior = np.round(points['exterior']).astype('int')
            interiors = [np.round(x).astype('int') for x in points['interior']]

            # Do the crop before creating masked image

            [cmin,rmin] = exterior.min(axis=0)
            [cmax,rmax] = exterior.max(axis=0)
            exterior_offset = exterior - exterior.min(axis=0)
            
            img_masked = np.zeros((rmax-rmin,cmax-cmin,4), dtype=np.uint8)
            # img_mask_only = np.zeros((rmax-rmin,cmax-cmin,4), dtype=np.uint8)
            mask_full = to_uint8_mask(exterior, interiors, img.shape[:2])
            mask = mask_full[slice(rmin,rmax), slice(cmin,cmax)]

            img_masked[:,:,:3] = img[slice(rmin,rmax), slice(cmin,cmax), :3]
            img_masked[:,:,3] = mask
            
            # Copying mask image into four channels of RGBA
            # https://stackoverflow.com/questions/32171917/copy-2d-array-into-3rd-dimension-n-times-python
            # This is the same thing as creating an empty 4-channel image array and copying
            #   the mask array into all four channels separately, but wanted to know how
            #   to do this in a fancy Numpy way with np.broadcast_to()
            # Note: if xx.shape == (3,2), xx[...,None].shape == (3,2,1)
            #   and (3,2)+(4,) == (3,2,4)
            
            # img_mask_only = np.zeros((rmax-rmin,cmax-cmin,4), dtype=np.uint8)
            # img_mask_only[:,:,0] = mask
            # img_mask_only[:,:,1] = mask
            # img_mask_only[:,:,2] = mask
            # img_mask_only[:,:,3] = mask
            
            img_mask_only = np.broadcast_to(mask[...,None], mask.shape+(4,))

        # --- Bitmap

        elif geometry_type == 'bitmap':
        
            bitmap = ob['bitmap']
            mask = base64_2_mask(bitmap['data'])
            rr,cc = mask.shape
            cc0,rr0 = bitmap['origin']

            img_masked = np.zeros((rr,cc,4), dtype=np.uint8)

            img_masked[:,:,:3] = img[slice(rr0,rr0+rr), slice(cc0,cc0+cc), :3]
            img_masked[:,:,3] = mask        
            img_mask_only = np.broadcast_to(mask[...,None], mask.shape+(4,))
        
        # --- Not handling anything beyond Polygon or Bitmap for now
        
        else:
            continue

        # Save mask file
        mask_name = img_name+'_'+str(ob['classId'])+'_'+str(ob['id'])+'.png'
        skio.imsave(os.path.join(mask_path, mask_name), img_mask_only)

        # Save masked feature image file
        masked_feature_name = img_name+'_'+str(ob['classId'])+'_'+str(ob['id'])+'.png'
        skio.imsave(os.path.join(masked_feature_path, masked_feature_name), img_masked)
