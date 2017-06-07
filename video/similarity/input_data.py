#coding=utf-8
import os
import cv2
import random
import numpy as np

image_height = 256
image_width = 256

def get_image_list(file_dir):
    if not os.path.exists(file_dir):
        raise IOError("file dir does not exist")
    images = os.listdir(file_dir)
    images.sort(key= lambda x:int(x[:-4]))
    return images

def get_random_image(image_name, images_list):
    list_len = len(images_list)
    rand_index = random.randint(0, list_len-1)
    if image_name != images_list[rand_index]:
        return images_list[rand_index]
    else:
        return get_random_image(image_name, images_list)

def merge_shuffle(pos_data, neg_data):
    train_data = np.concatenate((pos_data, neg_data), axis=0)

    pos_label = np.ones((pos_data.shape[0],2), dtype=np.int32)
    pos_label[:,1] = 0
    neg_label = np.zeros((neg_data.shape[0],2), dtype=np.int32)
    neg_label[:,1] = 1
    train_label = np.concatenate((pos_label, neg_label), axis=0)

    num = train_data.shape[0]
    perm = np.arange(num)
    np.random.shuffle(perm)
    train_data = train_data[perm]
    train_label = train_label[perm]
    return train_data, train_label

def next_batch(type, double_batch_size, batch_index):
    if type == 'train':
        raw_file = 'dataset/train/raw'
        copy_file = 'dataset/train/copy'
    else:
        raw_file = 'dataset/test/raw'
        copy_file = 'dataset/test/copy'

    iter_add = 0
    batch_size = double_batch_size / 2
    raw_images = get_image_list(raw_file)
    copy_images = get_image_list(copy_file)
    raw_images_len = len(raw_images)
    copy_images_len = len(copy_images)

    if raw_images_len != copy_images_len:
        raise IOError("dataset is imcompleted")

    if batch_size > raw_images_len:
        raise ValueError("batch size was biger than image number")

    if batch_index + batch_size < raw_images_len:
        batch_start = batch_index
        batch_end = batch_index + batch_size
        font_images = raw_images[batch_start:batch_end]
        later_pos_images = copy_images[batch_start:batch_end]
    else:
        batch_start = batch_index
        batch_end = (batch_index + batch_size) % raw_images_len
        font_images = raw_images[batch_start:]
        font_images.extend(raw_images[:batch_end])
        later_pos_images = copy_images[batch_start:]
        later_pos_images.extend(copy_images[:batch_end])
        iter_add += 1


    batch_index = batch_end

    later_neg_images = []
    for name in font_images:
        random_image_name = get_random_image(name, raw_images)
        later_neg_images.append(random_image_name)

    pos_data = np.zeros((batch_size, image_height, image_width, 6))
    neg_data = np.zeros((batch_size, image_height, image_width, 6))

    for index in range(batch_size):
        font_image_path = os.path.join(raw_file,font_images[index])
        later_pos_image_path = os.path.join(copy_file,later_pos_images[index])
        later_neg_image_path = os.path.join(raw_file,later_neg_images[index])


        font_image = cv2.imread(font_image_path)
        later_pos_image = cv2.imread(later_pos_image_path)
        later_neg_image = cv2.imread(later_neg_image_path)

        np_font_image = np.array(font_image, dtype=np.float32)
        np_later_pos_image = np.array(later_pos_image, dtype=np.float32)
        np_later_neg_image = np.array(later_neg_image, dtype=np.float32)

        pos_data[index,:,:,0:3] = np_font_image
        pos_data[index,:,:,3:6] = np_later_pos_image
        neg_data[index,:,:,0:3] = np_font_image
        neg_data[index,:,:,3:6] = np_later_neg_image

    train_data, train_label = merge_shuffle(pos_data, neg_data)
    return train_data/255., train_label, batch_index, iter_add






if __name__ == '__main__':
#    get_image_list('dataset/raw')
    next_batch(64, 2700)