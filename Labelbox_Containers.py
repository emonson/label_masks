# coding: utf-8

#
#  This code assumes that Labelbox_Masks.py has already been run, so all of the
#  mask images have been downloaded locally
#

from skimage import io
import json
import os
import numpy as np
# from timeit import default_timer as timer

# Making a non-complete threshold for pixel overlap in case a few pixels are outside
containment_threshold = 0.98

json_file = 'export-2020-07-23T01_23_49.887Z.json'
output_json_file = 'export-2020-07-23T01_23_49.887Z_instance.json'
data_dir = os.path.join('.','LabelboxMasks')

json_path = os.path.join(data_dir,json_file)
mask_dir = os.path.join(data_dir,'masks')

# ### Labelbox JSON Schema
# 
# - **annotations** : JSON list of objects, one per labeled image (book page)
# - **External ID** : name of the image
# - **Labeled Data** : URI of the image
# - **Label** : Object containing all labels
#     - **objects** : List of all labeled feature objects
#         - **featureId** : unique ID for the feature *(used in the URI, and I'll use for a file name)*
#         - **instanceURI** : URI of the mask image *(exists for both polygons and bitmaps)*
#         - **polygon** : list of x,y objects containing the coordinates of the polygon vertices *(won't exist for a pure bitmap mask)*
#         - **title** : should be "containers" for container object
#         

def img_contained(container_img, feature_img, thresholdFraction):
    # Images are expected to be one-channel, boolean 0s and 1s of the same dimensions
    overlapSum = (container_img*feature_img).sum()
    # Returns True or False
    return overlapSum/feature_img.sum() > thresholdFraction

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

# https://stackoverflow.com/questions/40795709/checking-whether-two-rectangles-overlap-in-python-using-two-bottom-left-corners
def bbox_overlaps(bb1,bb2):
    return not (bb1[1][1] < bb2[1][0] or bb1[1][0] > bb2[1][1] or bb1[0][1] < bb2[0][0] or bb1[0][0] > bb2[0][1])
    # return not (self.top_right.x < other.bottom_left.x or self.bottom_left.x > other.top_right.x or self.top_right.y < other.bottom_left.y or self.bottom_left.y > other.top_right.y)

# Load JSON
with open(json_path,'r') as f:
    annotations = json.load(f)

for ann_idx, ann in enumerate(annotations):

    image_filename = ann['External ID']
    
    # This will be used as a subdirectory for masks and features
    img_subdir = image_filename.replace('.','_')
    print(image_filename)

    # Container images will be loaded into a list (really dictionary) since all others need to be
    # compared to all of those, but the rest of the mask images will be loaded
    # one at a time before comparison. 
    
    container_dict = {}
    container_bb_dict = {}
    # These IDs gave errors in download, so skipping here
    id_skip_list = ['ckb16dq3w00l80ya3b9b7bn7z']
    
    # First loop identifies and loads all containers 
    for obj in ann['Label']['objects']:

        mask_id = obj['featureId']
        if mask_id in id_skip_list: continue

        if 'container' in obj['title']:
            mask_path = os.path.join(mask_dir, img_subdir, mask_id+'.png')
            print('\t Reading container', mask_id, 'image from file')
            mask_img = io.imread(mask_path)
            container_dict[mask_id] = mask_img[:,:,3].astype(np.bool)   
            container_bb_dict[mask_id] = bbox2(container_dict[mask_id])     
        
    # Second loop loads in non-container masks and compares to all containers
    # Keep track of obj index, so can insert instance ID in proper place
    for obj_idx, obj in enumerate(ann['Label']['objects']):

        mask_id = obj['featureId']
        if mask_id in id_skip_list: continue

        if mask_id not in container_dict:
            print('\t Reading mask', mask_id, 'from file')
            mask_path = os.path.join(mask_dir, img_subdir, mask_id+'.png')
            mask_rgba = io.imread(mask_path)
            mask_img = mask_rgba[:,:,3].astype(np.bool)   
            mask_bb = bbox2(mask_img)     

            # Loop through all container images
            # start_time = timer()

            match_found = False
            for cont_id, cont_img in container_dict.items():
                # Do a really fast test first to see if the bounding boxes overlap
                # before doing the slower test for image pixel overlap
                if bbox_overlaps(container_bb_dict[cont_id], mask_bb):
                    # Now do the pixels overlap test
                    if img_contained(cont_img, mask_img, containment_threshold):
                        match_found = True
                        # This probably isn't necessary, but checking to make sure no container instance already
                        if 'instance' in annotations[ann_idx]['Label']['objects'][obj_idx]:
                            print('\n','PROBLEM:',mask_id)
                            print('already has container instance',annotations[ann_idx]['Label']['objects'][obj_idx]['instance'])
                            print('but also matches',cont_id)
                        else:
                            # Write parent container ID into object dictionary
                            annotations[ann_idx]['Label']['objects'][obj_idx]['instance'] = cont_id
                            print('*',cont_id,'contains',mask_id,'!')
                            # print('\t\t',timer()-start_time)
                            # Counting on there only being one match, so don't need to test the rest
                            break
            if not match_found:
                print('no container match found')

# Write out JSON after all instances have been recorded
with open(os.path.join(data_dir, output_json_file), 'w', encoding='utf-8') as f:
    json.dump(annotations, f, ensure_ascii=False, indent=4)