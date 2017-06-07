#coding=utf-8
from skvideo.io import vreader
import cv2
import os
import numpy as np
from PIL import Image
import imagehash
import redis
import urllib
import commands

threshold = 256*256*3*0.3
video_dir = 'temp/video'
#r0 = redis.Redis(host='10.172.42.176', port=6379, password="NUIh93ts")
r0 = redis.Redis(host='localhost', port=6379, db=4)
cover_rate = 0.5
sampling_frequency = 0.2

title_prefix = 'video_title_'
vid_prefix = 'video_id_'
imghash_prefix = 'video_imghash_'
fw = open('log/offline/k.txt', 'a')
def generate_keyframe(video_name):
    video_path = os.path.join(video_dir, video_name)
    if not os.path.exists(video_path):
        raise IOError("video does not exists")
    
    fps_command = "ffmpeg -i " + video_path + " 2>&1 | grep 'fps'"
    status, output = commands.getstatusoutput(fps_command)
    output_array = output.strip().split(',')
    fps = 0
    for metadata in output_array:
        if 'fps' in metadata:
            fps = int(metadata.replace('fps', '').strip())
    if fps == 0:
        return []
    sampling_index = int(sampling_frequency * fps)
    video = cv2.VideoCapture(video_path)
    last_frame_hashcode = ''
    index = -1
    imagehash_list = []
    ret,frame = video.read()
    while ret:
        index += 1
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (256, 256))
        frame = frame[53:200, 53:200]  
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        image_instance = Image.fromarray(image)
        hashcode = str(imagehash.phash(image_instance, hash_size=4))
            
        if hashcode != last_frame_hashcode: 
            imagehash_list.append(hashcode)
            last_frame_hashcode = hashcode
        ret, frame = video.read()
    video.release()
    return imagehash_list

def get_repeated(a,b):
    a_len = len(a)
    b_len = len(b)
    maplist = np.zeros((a_len, b_len))
    repeated = 0
    period = 0

    for i in range(a_len):
        for j in range(b_len):
            if a[i] == b[j]:
                maplist[i, j] = 1

    i = 0
    while i < a_len:
        constant = 0
        b_pos = 0
        for j in range(b_len):
            temp_constant = 0
            m = i
            n = j
            while m < a_len and n < b_len and maplist[m, n] == 1:
                temp_constant += 1
                m += 1
                n += 1
            if temp_constant > constant:
                constant = temp_constant
                b_pos = j
        if constant > 0:
            repeated += constant
            period += 1
        i += constant + 1
    return repeated, period

def get_likehood_ids(hashlist):
    ids_dict = {}
    likehood_ids = []
    number = len(hashlist)
    for hashcode in hashlist:
        isExists = r0.exists(imghash_prefix + hashcode)
        if isExists:
            ids = r0.lrange(imghash_prefix + hashcode, 0, -1)
            for id in ids:
                if ids_dict.has_key(id):
                    ids_dict[id] += 1
                else:
                    ids_dict[id] = 1
    # likehood_id = max(ids_dict.items(), key=lambda x:x[1])[0]
    # for (key, value) in ids_dict.items():
    #     if value < (number * cover_rate):
    #         del ids_dict[key]
    ids_dict = sorted(ids_dict.items(), key = lambda x:x[1], reverse=True)
    i = 1
    for (key, value) in ids_dict:
        if i > 10:
            break
        else:
            likehood_ids.append(key)
    return likehood_ids

#push video and imagehash to redis
def video_pushin(r_db, vid, vtitle, imghash_list):
    if not r_db.exists(vid_prefix + vid):
        r_db.set(title_prefix + vid, vtitle)
        for imghash in imghash_list:
            r_db.rpush(vid_prefix + vid, imghash)
            r_db.rpush(imghash_prefix + imghash, vid)

#download video file to temp/video
def downloadVideo(vurl):
    video_name = vurl.split('/')[-1]
    video_path = os.path.join(video_dir, video_name)
    if os.path.exists(video_path):
        return "video exists"
    try:
        urllib.urlretrieve(vurl, video_path)
    except:
        return 'download failed'
    return video_name

def deleteVideo(video_name):
    video_path = os.path.join(video_dir, video_name)
    if os.path.exists(video_path):
        os.remove(video_path)

def detect(vid, vurl, vtitle):
    if r0.exists(vid_prefix + vid):
        return {'code':400, 'rvideoid':vid,'msg':vid + ' ' + vtitle + " had detected"}
    video_name = downloadVideo(vurl)
    if video_name == 'video exists':
        return {'code':400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " is being processed"}
    elif video_name == 'download failed':
        file_name = vurl.split('/')[-1]
        deleteVideo(file_name)
        return {'code':400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " download failed"}

    try:
        imghash_list = generate_keyframe(video_name)
    except ValueError, e:
        deleteVideo(video_name)
        return {'code':400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " can't reader " + str(e)}
    except Exception,e:
        deleteVideo(video_name)
        return {'code': 400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " " + str(e)}
    deleteVideo(video_name)
    fw.write(vid + '\t' + ' '.join(imghash_list) + '\n')
    if len(imghash_list) == 0:
        return {'code':400, 'rvideoid':vid,'msg':"video has no hashcode"}
    elif len(imghash_list) <= 2:
        return {'code':200, 'rvideoid':vid, 'unique':1 ,'msg':"video is unique"}
    likehood_ids = get_likehood_ids(imghash_list)
    flag = 0
    for alter_id in likehood_ids:
        alter_imghash_list = r0.lrange(vid_prefix + alter_id, 0, -1)
        if float(len(imghash_list))/len(alter_imghash_list) > 3 or float(len(alter_imghash_list))/len(imghash_list) > 3:
            continue
        repeated, period = get_repeated(imghash_list, alter_imghash_list)
        threshold = 0.6
#        if float(repeated)/len(imghash_list) >= threshold and float(repeated)/len(alter_imghash_list) >= threshold:
        r_rate = float(repeated)/len(imghash_list)
        if r_rate >= threshold:
            flag = 1
            similar_video_id = alter_id
            break
    if flag == 0:
        video_pushin(r0, vid, vtitle, imghash_list)
        return {'code':200, 'rvideoid':vid, 'unique':1 ,'msg':"video is unique"}
    else:
        return {'code': 200, 'rvideoid':vid, 'unique':0, 'msg': "video is similar to video " + similar_video_id, 'similar_rvideoid':similar_video_id + '_' + str(r_rate)}

if __name__=="__main__":
    detect('VCITR4L2J', 'http://flv2.bn.netease.com/videolib3/1705/07/MEfdc5022/SD/MEfdc5022-mobile.mp4', 'none')
