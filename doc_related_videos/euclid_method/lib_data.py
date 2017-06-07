#coding=utf-8
import time
import datetime
import os
def load_lib_video_list(filedir):
    video_list = set()
    date_list = get_last_n_date(180)
    for i in date_list:
        filename = 'video_list_' + i
        filepath = os.path.join(filedir, filename)
        if not os.path.exists(filepath):
            continue
        fr = open(filepath)
        for line in fr.readlines():
            vid = line.strip()
            if vid == '':
                continue
            video_list.add(vid)
        fr.close()
    return video_list

def load_lib_video_data(filedir):
    video_data = []
    date_list = get_last_n_date(180)
    for i in date_list:
        filename = 'video_data_' + i
        filepath = os.path.join(filedir, filename)
        if not os.path.exists(filepath):
            continue
        fr = open(filepath)
        for line in fr.readlines():
            video = line.strip()
            if video == '':
                continue
            video_data.append(video)
        fr.close()
    return video_data

def load_lib_doc_list(filedir):
    doc_list = set()
    date_list = get_last_n_date(7)
    for i in date_list:
        filename = 'doc_list_' + i
        filepath = os.path.join(filedir, filename)
        if not os.path.exists(filepath):
            continue
        fr = open(filepath)
        for line in fr.readlines():
            docid = line.strip()
            if docid == '':
                continue
            doc_list.add(docid)
        fr.close()
    return doc_list

def load_lib_doc_data(filedir):
    doc_data = []
    date_list = get_last_n_date(7)
    for i in date_list:
        filename = 'doc_data_' + i
        filepath = os.path.join(filedir, filename)
        if not os.path.exists(filepath):
            continue
        fr = open(filepath)
        for line in fr.readlines():
            doc = line.strip()
            if doc == '':
                continue
            doc_data.append(doc)
        fr.close()
    return doc_data

def get_last_n_date(n):
    date_list = []
    now_time = datetime.datetime.now()
    for i in range(n-1):
        delta = -1 - i
        i_time = now_time + datetime.timedelta(days=delta)
        i_date = i_time.strftime('%Y%m%d')
        date_list.append(i_date)
    return date_list

def load_video_data():
    video_list = load_lib_video_list('data/video')
    video_data = load_lib_video_data('data/video')
    return video_list, video_data

def load_doc_data():
    doc_list = load_lib_doc_list('data/doc')
    doc_data = load_lib_doc_data('data/doc')
    return doc_list, doc_data

if __name__=='__main__':
    get_last_n_date(30)
