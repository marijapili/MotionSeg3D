#!/usr/bin/env python3
# Developed by Jiadai Sun
# 	and the main_funciton 'prosess_one_seq' refers to Xieyuanli Chen’s gen_residual_images.py
# This file is covered by the LICENSE file in the root of this project.
# Brief: This script generates residual images

import os
os.environ["OMP_NUM_THREADS"] = "4"
import yaml
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm
from icecream import ic
from common.dataset.utin3d.utils import load_poses, load_files, load_vertex

try:
    from c_gen_virtual_scan import gen_virtual_scan as range_projection
except:
    print("Using clib by $export PYTHONPATH=$PYTHONPATH:<path-to-library>")
    print("Currently using python-lib to generate range images.")
    from kitti_utils import range_projection


def check_and_makedirs(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def load_yaml(path):
    if yaml.__version__ >= '5.1':
        config = yaml.load(open(path), Loader=yaml.FullLoader)
    else:
        config = yaml.load(open(path))
    return config


def process_one_seq(config):
    # specify parameters
    num_frames = config['num_frames']
    debug = config['debug']
    normalize = config['normalize']
    num_last_n = config['num_last_n']
    visualize = config['visualize']
    visualization_folder = config['visualization_folder']

    # specify the output folders
    residual_image_folder = config['residual_image_folder']
    check_and_makedirs(residual_image_folder)

    if visualize:
        check_and_makedirs(visualization_folder)

    # load poses
    pose_file = config['pose_file']
    poses = np.array(load_poses(pose_file))

    # load LiDAR scans
    scan_folder = config['scan_folder']
    scan_paths = load_files(scan_folder)

    # test for the first N scans
    if num_frames >= len(poses) or num_frames <= 0:
        print('generate training data for all frames with number of: ', len(poses))
    else:
        poses = poses[:num_frames]
        scan_paths = scan_paths[:num_frames]

    range_image_params = config['range_image']

    # generate residual images for the whole sequence
    for frame_idx in tqdm(range(len(scan_paths))):
        name = scan_paths[frame_idx].split('/')[-1].replace('.ply', '.npy')
        file_name = os.path.join(residual_image_folder, name)
        diff_image = np.full((range_image_params['height'], range_image_params['width']), 0,
                       dtype=np.float32)  # [H,W] range (0 is no data)

        # for the first N frame we generate a dummy file
        if frame_idx < num_last_n:
            np.save(file_name, diff_image)
        else:
            # load current scan and generate current range image
            current_pose = poses[frame_idx]
            current_scan = load_vertex(scan_paths[frame_idx])
            current_range = range_projection(current_scan.astype(np.float32),
                                             range_image_params['height'], range_image_params['width'],
                                             range_image_params['fov_up'], range_image_params['fov_down'],
                                             range_image_params['max_range'], range_image_params['min_range'])[:, :, 3]

            # load last scan, transform into the current coord and generate a transformed last range image
            last_pose = poses[frame_idx - num_last_n]
            last_scan = load_vertex(scan_paths[frame_idx - num_last_n])
            last_scan_transformed = np.linalg.inv(current_pose).dot(last_pose).dot(last_scan.T).T
            last_range_transformed = range_projection(last_scan_transformed.astype(np.float32),
                                             range_image_params['height'], range_image_params['width'],
                                             range_image_params['fov_up'], range_image_params['fov_down'],
                                             range_image_params['max_range'], range_image_params['min_range'])[:, :, 3]

            # generate residual image
            valid_mask = (current_range > range_image_params['min_range']) & \
                            (current_range < range_image_params['max_range']) & \
                            (last_range_transformed > range_image_params['min_range']) & \
                            (last_range_transformed < range_image_params['max_range'])
            difference = np.abs(current_range[valid_mask] - last_range_transformed[valid_mask])

            if normalize:
                difference = np.abs(current_range[valid_mask] - last_range_transformed[valid_mask]) / current_range[valid_mask]

            diff_image[valid_mask] = difference

            if debug:
                fig, axs = plt.subplots(3)
                axs[0].imshow(last_range_transformed)
                axs[1].imshow(current_range)
                axs[2].imshow(diff_image, vmin=0, vmax=1)
                plt.show()

            if visualize:
                fig = plt.figure(frameon=False, figsize=(16, 10))
                fig.set_size_inches(20.48, 0.64)
                ax = plt.Axes(fig, [0., 0., 1., 1.])
                ax.set_axis_off()
                fig.add_axes(ax)
                ax.imshow(diff_image, vmin=0, vmax=1)
                image_name = os.path.join(visualization_folder, name)
                plt.savefig(image_name)
                plt.close()

            # save residual image
            np.save(file_name, diff_image)


if __name__ == '__main__':

    config_filename = 'config/data_preparing_utin3d.yaml'
    config = load_yaml(config_filename)

    # used for utin3d
    for dataroot, seqs, _ in next(os.walk(os.path.join(config['dataroot'], 'runs'))):

        for seq in seqs:
            for i in range(1,9): # residual_image_i

                # Update the value in config to facilitate the iterative loop
                config['num_last_n'] = i
                config['scan_folder'] = f"{config['dataroot']}/runs/{seq}/velodyne_frames"
                config['pose_file'] = f"{config['dataroot']}/annotation/{seq}/correct_traj_{seq}.pkl"
                config['residual_image_folder'] = f"{os.curdir}/residuals/{seq}/residual_images_{i}"
                config['visualization_folder'] = f"{os.curdir}/residuals/{seq}/visualization_{i}"
                ic(config)
                process_one_seq(config)
