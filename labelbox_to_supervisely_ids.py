# Hash string to 9-digit integer
# to go from Labelbox IDs to something that'll work in Supervisely

# https://stackoverflow.com/a/42089311

# Should check for ID collisions, not only over all Labelbox object IDs,
#   but also over all the existing Supervisely IDs if data sets will be merged

# Note: This method is for going from an arbitrary string to a 9-digit integer
#   There may be other methods that don't use hashlib since there are already
#   constraints on the original IDs with all lowercase and digits (base-36 int?)

import hashlib
import json
import os

def labelbox_to_supervisely_id(labelbox_id):
    hash_object = hashlib.sha256(labelbox_id.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    # The 16 is indicating that the original string is base-16
    int_dig = int(hex_dig, 16)
    # 10**9 returns an int while 1e9 returns a float
    supervisely_id = int_dig % 10**9
    return supervisely_id


json_file = 'export-2020-07-23T01_23_49.887Z.json'
data_dir = os.path.join('.','LabelboxMasks')
json_path = os.path.join(data_dir,json_file)


with open(json_path,'r') as f:
    annotations = json.load(f)

labelbox_ids_list = []
supervisely_ids_list = []

# Load in all IDs from Labelbox JSON
for ann in annotations:
    for obj in ann['Label']['objects']:
        labelbox_ids_list.append(obj['featureId'])

# Convert all to 9-digit integers
for lab_id in labelbox_ids_list:
    supervisely_ids_list.append(labelbox_to_supervisely_id(lab_id))

# Create a set out of the IDs list to check if all unique
supervisely_ids_set = set(supervisely_ids_list)
print('n_ids =', len(supervisely_ids_list), 'n_unique_ids =', len(supervisely_ids_set))

# n_ids = 9295 n_unique_ids = 9295
