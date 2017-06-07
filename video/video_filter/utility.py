#coding=utf-8
from skvideo.io import vreader
import cv2
import os
import numpy as np
from PIL import Image
import imagehash
import redis
import urllib

threshold = 256*256*3*0.5
video_dir = 'temp/video'
r0 = redis.Redis(host='10.172.42.176', port=6379, password="NUIh93ts")
#r0 = redis.Redis(host='localhost', port=6379, db=0)
cover_rate = 0.5
invalid_frame_hash = ['0000', '0100', '5555']
aijianji_frame_hash = ['3935', '0ff0', '55d4', '0fd4', '1f16', '7954']

title_prefix = 'video_title_'
vid_prefix = 'video_id_'
imghash_prefix = 'video_imghash_'

def generate_keyframe(video_name):
    video_path = os.path.join(video_dir, video_name)
    if not os.path.exists(video_path):
        raise IOError("video does not exists")
    
    video = cv2.VideoCapture(video_path)
    last_keyframe = np.zeros((11))
    last_frame = np.zeros((11))
    index = 1
    imagehash_list = []
    ret,frame = video.read()
    while ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (256, 256))
        hsvframe = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        current_frame = np.zeros((11))

        channel = hsvframe[:,:,0].reshape((256*256))
        # border_list = [0,23,46,71,156,187,279,331,360]
        border_list = [0., 11.5, 23., 35.5, 78., 93.5, 139.5, 165.5, 180.]
        h_hist = np.histogram(channel, bins=border_list, range=(0,360))[0] #[lift, right)
        h_hist[0] += h_hist[7]
        current_frame[:7] = h_hist[:7]

        channel = hsvframe[:, :, 1].reshape((256 * 256)) / 255.
        s_hist = np.histogram(channel, bins=[0.0, 0.65, 1.0], range=(0.0, 1.0))[0]
        current_frame[7:9] = s_hist

        channel = hsvframe[:, :, 2].reshape((256 * 256)) / 255.
        v_hist = np.histogram(channel, bins=[0.0, 0.7, 1.0], range=(0.0, 1.0))[0]
        current_frame[9:11] = v_hist

        diff1 = np.abs(current_frame - last_frame).sum()
        diff2 = np.abs(current_frame - last_keyframe).sum()

        if diff1 > threshold and diff2 > threshold:
            image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            image_instance = Image.fromarray(image)
            hashcode = str(imagehash.phash(image_instance, hash_size=4))
            
            if hashcode not in invalid_frame_hash:
                imagehash_list.append(hashcode)
                last_keyframe = current_frame
                index += 1
        last_frame = current_frame
        ret, frame = video.read()
    video.release()
    if len(imagehash_list) >= 6:
        if cmp(aijianji_frame_hash, imagehash_list[:6]) == 0:
            imagehash_list = imagehash_list[6:]
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
            # print('a: %d, b: %d, constant: %d' % (i,b_pos,constant))
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
    except ValueError:
        deleteVideo(video_name)
        return {'code':400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " can't reader " + str(e)}
    except Exception,e:
        deleteVideo(video_name)
        return {'code': 400, 'rvideoid':vid, 'msg':vid + ' ' + vtitle + " " + str(e)}
    deleteVideo(video_name)
    if len(imghash_list) <= 2:
        return {'code':200, 'rvideoid':vid, 'unique':1 ,'msg':"video is unique"}
    likehood_ids = get_likehood_ids(imghash_list)
    flag = 0
    for alter_id in likehood_ids:
        alter_imghash_list = r0.lrange(vid_prefix + alter_id, 0, -1)
        repeated, period = get_repeated(imghash_list, alter_imghash_list)
        # print repeated,period,len(imghash_list),len(alter_imghash_list)
        if len(imghash_list) <= 7:
            threshold = 1.0
        elif len(imghash_list) > 7:
            threshold = 0.8
        if float(repeated)/len(imghash_list) >= threshold and float(repeated)/len(alter_imghash_list) >= threshold:
            flag = 1
            similar_video_id = alter_id
            break
    if flag == 0:
        if len(imghash_list) > 2:
            video_pushin(r0, vid, vtitle, imghash_list)
        return {'code':200, 'rvideoid':vid, 'unique':1 ,'msg':"video is unique"}
    else:
#        video_pushin(r1, vid, vtitle, imghash_list)
        return {'code': 200, 'rvideoid':vid, 'unique':0, 'msg': "video is similar to video " + similar_video_id, 'similar_rvideoid':similar_video_id}

if __name__=="__main__":
    video_names = os.listdir(video_dir)
    for name in video_names:
        detect(name)
