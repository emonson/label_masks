# coding: utf-8

# ## Supervise.ly base64 bitmap to polygon

import numpy as np
import io
import os
import zlib
import json
import base64
import cv2
from skimage import io as skio
from skimage import measure
from skimage.measure import approximate_polygon, find_contours
from shapely.geometry import Polygon
from shapely.ops import unary_union

json_file = 'castelo_branco1.jpg.json'
output_json_file = 'castelo_branco1.jpg_poly.json'

data_dir = os.path.join('.','BOF_supervisely')
json_dir = os.path.join(data_dir,'ann')


def base64_2_mask(s):
    z = zlib.decompress(base64.b64decode(s))
    n = np.frombuffer(z, np.uint8)
    mask = cv2.imdecode(n, cv2.IMREAD_UNCHANGED)[:, :, 3]
    return mask

with open(os.path.join(json_dir,json_file), 'r', encoding='utf-8') as f:
    annotations = json.load(f)

n_objects = len(annotations['objects'])

for ii,ob in enumerate(annotations['objects']):
    if ob['geometryType'] == 'bitmap':

        print(ii,'/',n_objects)
        
        # Pop the bitmap dictionary element since we'll be replacing it
        bitmap = annotations['objects'][ii].pop('bitmap')
        img = base64_2_mask(bitmap['data'])
        origin = bitmap['origin']

        # embed image away from image boundaries
        # otherwise you'll just separate contours for all the black parts and not
        # a continuous outline for the entire object
        img_embed = np.zeros(tuple(x+2 for x in img.shape))
        img_embed[1:-1,1:-1] = img

        # Compute the contours
        contours = measure.find_contours(img_embed, 128)

        # Approximation – set tolerance to control number of points
        poly2_list = []
        for contour in contours:
            poly2_list.append(approximate_polygon(contour, tolerance=1.0))

        print('orig', sum([len(x) for x in contours]), 'pts : ',
              'appr', sum([len(x) for x in poly2_list]), 'pts')

        # Excluding anything that's not a polygon
        sh_poly2_list = [Polygon(x) for x in poly2_list if len(x) > 2]
        poly2_union = unary_union(sh_poly2_list)

        # NOTE: For now only doing exterior points!
        # NOTE: The problematic part here is that it will connect 
        #   multiple disconnected polygons into one, 
        #   so a path will be drawn between them...
        coords_in = None
        if poly2_union.geom_type == 'MultiPolygon':
            ar_list_ex = []
            ar_list_in = []
            for poly in poly2_union.geoms:
                ar_list_ex.append(np.array(poly.exterior.coords))
                # NOTE: not sure if this is really the right test if some interiors
                if len(list(poly.interiors)) > 0:
                    for ints in poly.interiors:
                        ar_list_in.append(np.array(ints.coords))
            coords_ex = np.concatenate(ar_list_ex, axis=0)
            if len(ar_list_in) > 0:
                coords_in = np.concatenate(ar_list_in, axis=0)
        elif poly2_union.geom_type == 'Polygon':
            coords_ex = np.array(poly2_union.exterior.coords)
            if len(list(poly2_union.interiors)) > 0:
                ar_list_in = []
                for ints in poly2_union.interiors:
                    print(ints)
                    ar_list_in.append(np.array(ints.coords))
                coords_in = np.concatenate(ar_list_in, axis=0)
        else:
            print('problem type')

        # Need to subtract one for the fake pixel offset, and add origin
        # origin seems to be in a strange order
        real_coords_ex = (coords_ex.round(2)-1) + np.array([origin[1],origin[0]])
        if coords_in is not None:
            real_coords_in = (coords_in.round(2)-1) + np.array([origin[1],origin[0]])

        # NOTE: X and Y need to be flipped for final output
        flipped_coords_ex = np.flip(real_coords_ex, axis=1)
        if coords_in is not None:
            flipped_coords_in = np.flip(real_coords_in, axis=1)
        
        # Create the new polygon
        # NOTE: For now only doing exterior points!
        annotations['objects'][ii]['geometryType'] = 'polygon'
        annotations['objects'][ii]['points'] = {'exterior':[], 'interior':[]}
        annotations['objects'][ii]['points']['exterior'] = flipped_coords_ex.tolist()
        if coords_in is not None:
            annotations['objects'][ii]['points']['interior'] = flipped_coords_in.tolist()

# Write out new JSON file
with open(os.path.join(json_dir,output_json_file), 'w', encoding='utf-8') as f:
    json.dump(annotations, f, ensure_ascii=False, indent=4)    
