#!/usr/bin/env python
"""
Copyright 2016 Yahoo Inc.
Licensed under the terms of the 2 clause BSD license. 
Please see LICENSE file in the project root for terms.
"""

import numpy as np
import os
import sys
import argparse
import glob
import time
from PIL import Image
from StringIO import StringIO
import caffe
import cv2
from skvideo.io import vreader,ffprobe

video_temp = 'temp/video'
image_temp = 'temp/image'

interval = 5

def resize_image(data, sz=(256, 256)):
    """
    Resize image. Please use this resize logic for best results instead of the 
    caffe, since it was used to generate training dataset 
    :param str data:
        The image data
    :param sz tuple:
        The resized image dimensions
    :returns bytearray:
        A byte array with the resized image
    """
    img_data = str(data)
    im = Image.open(StringIO(img_data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=Image.BILINEAR)
    fh_im = StringIO()
    imr.save(fh_im, format='JPEG')
    fh_im.seek(0)
    return bytearray(fh_im.read())

def caffe_preprocess_and_compute(pimg, caffe_transformer=None, caffe_net=None,
    output_layers=None):
    """
    Run a Caffe network on an input image after preprocessing it to prepare
    it for Caffe.
    :param PIL.Image pimg:
        PIL image to be input into Caffe.
    :param caffe.Net caffe_net:
        A Caffe network with which to process pimg afrer preprocessing.
    :param list output_layers:
        A list of the names of the layers from caffe_net whose outputs are to
        to be returned.  If this is None, the default outputs for the network
        are returned.
    :return:
        Returns the requested outputs from the Caffe net.
    """
    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(StringIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = max((H - h) / 2, 0)
        w_off = max((W - w) / 2, 0)
        crop = image[h_off:h_off + h, w_off:w_off + w, :]
        transformed_image = caffe_transformer.preprocess('data', crop)
        transformed_image.shape = (1,) + transformed_image.shape

        input_name = caffe_net.inputs[0]
        all_outputs = caffe_net.forward_all(blobs=output_layers,
                    **{input_name: transformed_image})

        outputs = all_outputs[output_layers[0]][0].astype(float)
        return outputs
    else:
        return []


def main(video_dict):
    model_def = 'nsfw_model/deploy.prototxt'
    pretrained_model = 'nsfw_model/resnet_50_1by2_nsfw.caffemodel'

    pycaffe_dir = os.path.dirname(__file__)
    
    # Pre-load caffe model.
    nsfw_net = caffe.Net(model_def,  # pylint: disable=invalid-name
        pretrained_model, caffe.TEST)

    # Load transformer
    # Note that the parameters are hard-coded for best results
    caffe_transformer = caffe.io.Transformer({'data': nsfw_net.blobs['data'].data.shape})
    caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
    caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
    caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
    caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR
    
    if not os.path.exists(image_temp):
        os.mkdir(image_temp)
        
    if not os.path.exists(video_temp):
        os.mkdir(video_temp)
    
    conclusion_dict = {}
    
    for video_name in video_dict:
        video_path = os.path.join(video_temp, video_name)
        if not os.path.exists(video_path):
            continue
            
        image_files = os.listdir(image_temp)
        if len(image_files) > 0:
            for filename in image_files:
                filepath = os.path.join(image_temp, filename)
                os.remove(filepath)
        
        metadata = ffprobe(video_path) 
        avg_frame_rate = metadata["video"]["@avg_frame_rate"].split('/')
        rate = int(avg_frame_rate[0])/int(avg_frame_rate[1])
        video = vreader(video_path)
    
        index = 0
        for frame in video:
            if index % (rate*interval) == 0:
                img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(image_temp + '/' + str(index/rate) + '.jpg', img)
            index += 1

        # fetch all image score.
        safe_count = 0
        danger_count = 0
        warning_count = 0
        middle_count = 0
        danger_list = []
        warning_list = []
        scores_list = np.array([])
        
        image_files = os.listdir(image_temp)
        for image_name in image_files:
                second = image_name.split('.')[0]
                image_path = os.path.join(image_temp, image_name)
                image_data = open(image_path).read()
                scores = caffe_preprocess_and_compute(image_data, caffe_transformer=caffe_transformer, caffe_net=nsfw_net, output_layers=['prob'])
                if scores[1] > 0.8:
                    danger_count += 1
                    danger_list.append(second)
                elif scores[1] > 0.5:
                    warning_count += 1
                    middle_count += 1
                    warning_list.append(second)
                elif scores[1] > 0.2:
                    middle_count += 1
                else:
                    safe_count += 1
                scores_list = np.append(scores_list, scores[1])
        # Scores is the array containing SFW / NSFW image probabilities
        # scores[1] indicates the NSFW probability

        conclusion_dict[video_name] = {
            'url':video_dict[video_name],
            'name':video_name.split('.')[0],
            'extension':video_name.split('.')[-1],
            'total_count':scores_list.shape[0],
            'danger_count':danger_count,
            'warning_count':warning_count,
            'danger_second':danger_list,
            'warning_second':warning_list,
        }
        print("video name: %s, total: %d, danger_count: %d, warning_count: %d" % (video_name, scores_list.shape[0], danger_count, warning_count))
        os.remove(video_path)
    return conclusion_dict



if __name__ == '__main__':
    input_file = '1.MP4'
    main(input_file)
