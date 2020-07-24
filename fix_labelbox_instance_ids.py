#!/usr/bin/env python
# coding: utf-8

#
#  This should be run after Labelbox_Containers.py since that script currently
#  assigns the container ID to all of its children, but Supervisely has a parent-less
#  model without containers, where one of the siblings acts as a parent (also to itself)
#

import json
import os

json_file = 'export-2020-07-23T01_23_49.887Z_instance.json'
output_json_file = 'export-2020-07-23T01_23_49.887Z_instanceFixed.json'
data_dir = os.path.join('.','LabelboxMasks')
json_path = os.path.join(data_dir,json_file)


with open(json_path,'r') as f:
    annotations = json.load(f)

# Loop through all annotated images
for ann_idx, ann in enumerate(annotations):
    
    container_dict = {}
    
    # There are many ways to do this – I'm just going to do multiple passes throug
    # the objects since these are all super fast operations
    # First loop creates container lookup dictionary of lists
    for obj in ann['Label']['objects']:
        mask_id = obj['featureId']

        if 'container' in obj['title']:
            container_dict[mask_id] = [] 

    # Second loop loads feature (index,id) pairs into a list of the container's children
    for obj_idx, obj in enumerate(ann['Label']['objects']):
        mask_id = obj['featureId']

        # Only non-container objects should have 'instance'
        if 'instance' in obj:
            container_dict[obj['instance']].append((obj_idx, mask_id))
    
    # print(ann['External ID'])
    # print(container_dict)
    # print('\n')

    # Go through each container
    # If it has children, pick the first child ID and copy it to all child 'instance' fields
    for cont_id, child_tuples_list in container_dict.items():
        if len(child_tuples_list) > 0:
            new_instance_id = child_tuples_list[0][1]
            
            for child_idx, child_id in child_tuples_list:
                annotations[ann_idx]['Label']['objects'][child_idx]['instance'] = new_instance_id
        
# Write out JSON after all instances have been recorded
with open(os.path.join(data_dir, output_json_file), 'w', encoding='utf-8') as f:
    json.dump(annotations, f, ensure_ascii=False, indent=4)