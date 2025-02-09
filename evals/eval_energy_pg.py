# -- coding: utf-8 --**

"""
Created on 2024/10/25

@author: Ruoyu Chen
"""

import argparse

import os
import os
import json
import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image

from tqdm import tqdm

from sklearn import metrics

import math

def parse_args():
    parser = argparse.ArgumentParser(description='Energy Point Game')
    parser.add_argument('--Datasets',
                        type=str,
                        default='datasets/coco/val2017',
                        help='Datasets.')
    parser.add_argument('--explanation-dir', 
                        type=str, 
                        default='baseline_results/tradition-detector-coco-correctly/yolo_v3-DRISE',
                        help='Save path for saliency maps generated by our methods.')
    args = parser.parse_args()
    return args

def add_value(S_set, json_file):
    single_mask = np.zeros_like(S_set[0])
    single_mask = single_mask.astype(np.float16)
    
    value_list_1 = np.array(json_file["smdl_score"])
    
    value_list_2 = np.array(
        [1-json_file["org_score"]+json_file["baseline_score"]] + json_file["smdl_score"][:-1]
    )
    
    value_list = value_list_1 - value_list_2
    
    values = []
    value = 0
    i = 0
    for smdl_single_mask, smdl_value in zip(S_set, value_list):
        value = value - abs(smdl_value)
        single_mask[smdl_single_mask==1] = value
        values.append(value)
        
        i+=1
    attribution_map = single_mask - single_mask.min()
    attribution_map = attribution_map / attribution_map.max()
    
    return attribution_map, np.array(values)

def energy_point_game(bbox, saliency_map):
  
    x1, y1, x2, y2 = bbox
    w, h = saliency_map.shape

    empty = np.zeros((w, h))
    empty[y1:y2, x1:x2] = 1
    mask_bbox = saliency_map * empty

    energy_bbox =  mask_bbox.sum()
    energy_whole = saliency_map.sum() + 0.000000000001

    proportion = energy_bbox / energy_whole
    return proportion

def point_game(bbox, saliency_map):
  
    x1, y1, x2, y2 = bbox
    w, h = saliency_map.shape

    empty = np.zeros((w, h))
    empty[y1:y2, x1:x2] = 1
    mask_bbox = saliency_map * empty
    
    if mask_bbox.max() == saliency_map.max():
        return 1
    else:
        return 0

def main(args):
    print(args.explanation_dir)
    
    json_root_file = os.path.join(args.explanation_dir, "json")
    npy_root_file = os.path.join(args.explanation_dir, "npy")
    json_file_names = os.listdir(json_root_file)
    
    pg_value = []
    pg_energy_value = []
    
    for json_file_name in tqdm(json_file_names):
        json_file_path = os.path.join(json_root_file, json_file_name)
        npy_file_path = os.path.join(npy_root_file, json_file_name.replace(".json", ".npy"))
        if "_" in json_file_name:
            if "COCO_train2014" in json_file_name:
                image_path = os.path.join(args.Datasets, json_file_name.replace("_"+json_file_name.split("_")[-1],"")+".jpg")
                # print(image_path)
            elif "train" in json_file_name or "val" in json_file_name:
                image_path = os.path.join(args.Datasets, json_file_name.split("_")[0] + "/" + json_file_name.split("_")[1]+".jpg")
            else:
                image_path = os.path.join(args.Datasets, json_file_name.split("_")[0]+".jpg")
        else:
            image_path = os.path.join(args.Datasets, json_file_name.replace(".json", ".jpg"))
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            saved_json_file = json.load(f)
        
        image = cv2.imread(image_path)
        
        if "submodular" in npy_file_path:
            S_set = np.load(npy_file_path)
            attribution_map, _ = add_value(S_set, saved_json_file)
            
            attribution_map = cv2.resize(attribution_map.astype(float), (image.shape[1], image.shape[0]))
            
        else:
            attribution_map = np.load(npy_file_path)
            if math.isnan(attribution_map.min()):
                # print("bad")
                pg_energy_value.append(0)
                pg_value.append(0)
                continue
            attribution_map = attribution_map - attribution_map.min()
            attribution_map = attribution_map / (attribution_map.max() + 0.00000001)
        
        bbox = saved_json_file["target_box"]
        
        en_pg = energy_point_game(bbox, attribution_map)
        pg = point_game(bbox, attribution_map)

        pg_energy_value.append(en_pg)
        pg_value.append(pg)
    
    print("Point Game: {}".format(np.array(pg_value).mean()))
    print("Energy Point Game: {}".format(np.array(pg_energy_value).mean()))

if __name__ == "__main__":
    args = parse_args()
    main(args)