#coding=utf-8
import os
import shutil
import zipfile
from skvideo.io import vreader,ffprobe
import cv2

video_extension = ['.avi', '.mp4', '.mpeg', '.mov', '.mpg', '.rmvb', '.wmv', '.mkv']
interval = 30
image_height = 256
image_width = 256

train_raw_file = "dataset/train/raw/"
train_copy_file = "dataset/train/copy/"

test_raw_file = "dataset/test/raw/"
test_copy_file = "dataset/test/copy/"

def unzip_file(file_dir, target_dir):
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.mkdir(target_dir)
    zipfiles = os.listdir(file_dir)
    for filename in zipfiles:
        file_path = os.path.join(file_dir, filename)
        if zipfile.is_zipfile(file_path):
            zip_file = zipfile.ZipFile(file_path, 'r')
            zip_file.extractall(target_dir)
    print("success")

def choose_video(file_dir):
    if os.path.exists(file_dir) == False:
        raise ValueError("file_dir does not exist")
    filenames = os.listdir(file_dir)
    for filename in filenames:
        file_path = os.path.join(file_dir, filename)
        if os.path.isdir(file_path):
            choose_video(file_path)
        else:
            extension = os.path.splitext(file_path)[-1].lower()
            if extension in video_extension:
                utf8name = filename.decode('gbk')
                print utf8name
                shutil.copy(file_path, 'video/'+ utf8name)

def generate_dataset(video_dir):
    if not os.path.exists(video_dir):
        raise ValueError("video dir does not exist")
    video_files = os.listdir(video_dir)
    image_index = 1
    # for i in video_files:
    #     print i.decode('utf8')
    # exit()
    for video in video_files:
        if 'rmvb' in video:
            continue
        print video
        video_path = os.path.join(video_dir, video)
        metadata = ffprobe(video_path)
        frame_info = metadata["video"]["@avg_frame_rate"].split('/')
        rate = int(frame_info[0])/int(frame_info[1])

        try:
            frame_array = vreader(video_path)
            frame_index = 0
            for frame in frame_array:
                if frame_index % (rate * interval) == 0:
                    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    image = cv2.resize(image, (image_height, image_width))
                    cv2.imwrite(test_raw_file + str(image_index) + '.jpg', image)
                    cv2.imwrite(test_copy_file + str(image_index) + '.jpg', image)
                    print("write image %d" % image_index)
                    image_index += 1
                elif frame_index % (rate * interval) == 1:
                    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    image = cv2.resize(image, (image_height, image_width))
                    cv2.imwrite(test_copy_file + str(image_index -1) + '.jpg', image)
                frame_index += 1
        except RuntimeError:
            continue

def image_resize(file_dir):
    if not os.path.exists(file_dir):
        raise ValueError("file dir does not exist")
    images = os.listdir(file_dir)
    for image_name in images:
        image_path = os.path.join(file_dir, image_name)
        image = cv2.imread(image_path)
        image = cv2.resize(image, (image_height, image_width))
        cv2.imwrite(image_path, image)



if __name__=='__main__':
#    unzip_file('sp','unzip')
#    choose_video('data/test/')
    generate_dataset('dataset/test/video')
#    image_resize('dataset/raw')
#    image_resize('dataset/copy')