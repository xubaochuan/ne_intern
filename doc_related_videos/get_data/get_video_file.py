#coding=utf-8
from rediscluster import StrictRedisCluster
import redis
import time
import datetime

def get_list(date):
    r = redis.Redis(host='10.200.131.27', port=6000, password='kji93tzs')
    key_prefix = 'headline_fresh_video_'
    all_video = set()
    filepath = '../normal_knn/jobs/data/video/video_list_' + date
    fw = open(filepath, 'w')
    key = key_prefix + date
    result = r.smembers(key)
    for i in result:
        if i not in all_video:
            all_video.add(i)
            fw.write(i + '\n')
    fw.close()
    return all_video

def get_video_data(date):
    video_keys = get_list(date)
    redis_nodes = [{'host':'10.200.131.32','port':6101},{'host':'10.200.131.31','port':6102},{'host':'10.200.131.27','port':6101},{'host':'10.200.131.28','port':6102}]
    r = StrictRedisCluster(startup_nodes=redis_nodes)
    filepath = '../normal_knn/jobs/data/video/video_data_' + date
    fw = open(filepath, 'w')
    key_prefix = 'headline_'
    for v_key in video_keys:
        key = key_prefix + v_key
        video = r.get(key)
        if isinstance(video, basestring):
            fw.write(video + '\n')
    fw.close()

def get_last_n_date(n):
    date_list = []
    now_time = datetime.datetime.now()
    for i in range(n-1):
        delta = -1 - i
        i_time = now_time + datetime.timedelta(days=delta)
        i_date = i_time.strftime('%Y%m%d')
        date_list.append(i_date)
    return date_list

if __name__=='__main__':
    date_list = get_last_n_date(180)
    date_list = ['20170513', '20170514']
    for date in date_list:
        get_video_data(date)
