#coding=utf-8
from rediscluster import StrictRedisCluster
import redis
import time
import datetime

def get_video_list(date):
    r = redis.Redis(host='10.200.131.27', port=6000, password='kji93tzs')
    key_prefix = 'headline_fresh_video_'
    video_list = set()
    filepath = 'data/video/video_list_' + date
    fw = open(filepath, 'w')
    key = key_prefix + date
    result = r.smembers(key)
    for i in result:
        if i not in video_list:
            fw.write(i + '\n')
            video_list.add(i)
    fw.close()
    return video_list

def get_video_data():
    timestamp = time.time()
    ltime=time.localtime(timestamp)
    date = time.strftime("%Y%m%d", ltime)
    video_list = get_video_list(date)
    redis_nodes = [{'host':'10.200.131.32','port':6101},{'host':'10.200.131.31','port':6102},{'host':'10.200.131.27','port':6101},{'host':'10.200.131.28','port':6102}]
    r = StrictRedisCluster(startup_nodes=redis_nodes)
    key_prefix = 'headline_'
    filepath = 'data/video/video_data_' + date
    fw = open(filepath, 'w')
    video_data = []
    for v_key in video_list:
        key = key_prefix + v_key
        video = r.get(key)
        if isinstance(video, basestring):
            fw.write(video + '\n')
            video_data.append(video)
    fw.close()
    return video_list, video_data

def get_doc_list(date):
    r = redis.Redis(host='10.200.131.27', port=6000, password='kji93tzs')
    key_prefix = 'headline_fresh_doc_'
    doc_list = set()
    filepath = 'data/doc/doc_list_' + date
    fw = open(filepath, 'w')
    key = key_prefix + date
    result = r.smembers(key)
    for i in result:
        if i not in doc_list:
            fw.write(i + '\n')
            doc_list.add(i)
    fw.close()
    return doc_list

def get_doc_data():
    timestamp = time.time()
    ltime=time.localtime(timestamp)
    date = time.strftime("%Y%m%d", ltime)
    doc_list = get_doc_list(date)
    redis_nodes = [{'host':'10.200.131.32','port':6101},{'host':'10.200.131.31','port':6102},{'host':'10.200.131.27','port':6101},{'host':'10.200.131.28','port':6102}]
    r = StrictRedisCluster(startup_nodes=redis_nodes)
    key_prefix = 'headline_'
    filepath = 'data/doc/doc_data_' + date
    fw = open(filepath, 'w')
    doc_data = []
    for d_key in doc_list:
        key = key_prefix + d_key
        doc = r.get(key) 
        if isinstance(doc, basestring):
            fw.write(doc + '\n')
            doc_data.append(doc)
    fw.close()
    return doc_list, doc_data

if __name__=='__main__':
    get_video_data()
    get_doc_data()
