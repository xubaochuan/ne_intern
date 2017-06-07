#coding=utf-8
import jieba
import numpy as np
from math import sqrt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import sys 
import json
import redis_data
import lib_data
import os
import time
reload(sys) 
sys.setdefaultencoding('utf8')
timestamp = int(time.time())
timestamp = timestamp / 100 * 100
jieba.load_userdict('model/dict.txt')

def load_wordvec():
    filepath = 'model/wordvec.txt'
    word2vec = {}
    fr = open(filepath)
    for line in fr.readlines():
        line_list = line.rstrip().split(' ')
        if len(line_list) != 201:
            continue
        word = line_list[0]
        vec = line_list[1:]
        for d in vec:
            d = float(d)
        word2vec[word] = vec
    fr.close()
    return word2vec

def load_stop_words(filepath = 'model/stop_dict.txt'):
    stop_word_set = set()
    fr = open(filepath)
    for line in fr.readlines():
        if line.strip() == '':
            continue
        stop_word_set.add(line.strip())
    fr.close()
    return stop_word_set 

def get_title_vec(title):
    seg_list = jieba.cut(title)
    wordvec_list = []
    for seg_word in seg_list:
        word = seg_word.encode('utf-8')
        if word in stop_words:
            continue
        if word not in word2vec:
            continue
        wordvec = word2vec[word]
        wordvec_list.append(wordvec)
    if len(wordvec_list) > 0:
        wordvec_array = np.asarray(wordvec_list, dtype=np.float32)
        title_vec = np.mean(wordvec_array, axis=0)
        return title_vec
    else:
        return 'empty'

def inverted_index(video_dict):
    ii_dict = {}
    for docid, array in video_dict.items():
        tags = array['dkeys']
        for r_tag in tags:
            tag = r_tag.encode('utf-8')
            if len(tag) <=3:
                continue
            if tag not in ii_dict:
                ii_dict[tag] = set()
            ii_dict[tag].add(docid)
    return ii_dict

def get_related_video(ii_dict, tags):
    result = set()
    for r_tag in tags:
        tag = r_tag.encode('utf-8')
        if tag in ii_dict:
            for title in ii_dict[tag]:
                result.add(title)
    return result 

def load_video_vec(titles):
    video_list = []
    title_list = []
    for line in titles:
        if line.strip() == '':
            continue
        video_vec_list = get_title_vec(line.strip())
        if isinstance(video_vec_list, basestring): 
            continue
        video_list.append(video_vec_list)
        title_list.append(line.strip())
    return title_list, video_list

def get_video_dict(video_data):
    video_dict = {}
    for video_json in video_data:
        video_array = json.loads(video_json.encode('utf-8'))
        if 'docid' not in video_array or 'title' not in video_array or 'dkeys' not in video_array:
            continue
        docid = video_array['docid']
        if docid in video_dict:
            continue
        title = video_array['title']
        dkeys = video_array['dkeys'].split(',')
        vec = get_title_vec(title)
        if isinstance(vec, basestring):
            continue
        video_dict[docid] = {'title': title, 'dkeys': dkeys, 'vec': vec}
    return video_dict

def get_doc_dict(doc_data):
    doc_dict = {}
    for doc_json in doc_data:
        doc_array = json.loads(doc_json.encode('utf-8'))
        if 'docid' not in doc_array or 'title' not in doc_array or 'dkeys' not in doc_array:
            continue
        docid = doc_array['docid']
        if docid in doc_dict:
            continue
        title = doc_array['title']
        dkeys = doc_array['dkeys'].split(',')
        vec = get_title_vec(title)
        if isinstance(vec, basestring):
            continue
        doc_dict[docid] = {'title': title, 'dkeys': dkeys, 'vec': vec}
    return doc_dict
        

word2vec = load_wordvec()
stop_words = load_stop_words()

def related_video_test():
    ii_dict = inverted_index()
    filepath = 'data/doc_topic.txt'
    fr = open(filepath)
    fw = open('data/result.txt', 'w')
    doc_titles = []
    doc_topics = []
    for line in fr.readlines():
        line_list = line.strip().split('\t')
        if '\t' not in line or len(line_list) != 3:
            continue
        doc_titles.append(line_list[1])
        doc_topics.append(line_list[2].strip().split(' '))
    num = len(doc_topics)
    for i in range(num):
        title = doc_titles[i]
        topics = doc_topics[i]
        related_video = get_related_video(ii_dict, topics)
        if len(related_video) == 0:
            continue
        v_title_list, v_video_list = load_video_vec(related_video)
        v_count = len(v_title_list)
        if v_count == 0:
            continue
        doc_vec_list = get_title_vec(title)
        if isinstance(doc_vec_list, basestring):
            continue
        max_sim = 0.0
        index = -1
        distance = cosine_similarity([doc_vec_list], v_video_list)
        for i in range(v_count):
            if distance[0][i] > max_sim:
                index = i
                max_sim = distance[0][i]
        fw.write(title + '\t' + ' '.join(topics) + '\t' + v_title_list[index] + '\t' + str(max_sim) + '\n')
        fw.flush()
    fr.close()
    fw.close()

def euclidean_distance(vec1_list, vec2_list):
    scores = []
    for vec1 in vec1_list:
        one_scores = []
        for vec2 in vec2_list:
            dist = np.sqrt(np.sum(np.square(vec1 - vec2)))
            one_scores.append(dist)
        scores.append(one_scores)
    return scores

def main():
    today_video_list, today_video_data = redis_data.get_video_data()
    today_doc_list, today_doc_data = redis_data.get_doc_data()
    lib_video_list, lib_video_data = lib_data.load_video_data()
    lib_doc_list, lib_doc_data = lib_data.load_doc_data()
    video_data = today_video_data + lib_video_data
    doc_data = today_doc_data + lib_doc_data
    video_dict = get_video_dict(video_data)
    doc_dict = get_doc_dict(doc_data)
    ii_dict = inverted_index(video_dict)
    log_filepath = 'result/log/log_' + str(timestamp)
    index_filepath = 'result/index/index_' + str(timestamp)
    fw_log = open(log_filepath, 'w')
    fw_index = open(index_filepath, 'w')
    for docid, array in doc_dict.items():
        tags = array['dkeys']
        related_video = get_related_video(ii_dict, tags)
        if len(related_video) == 0:
            continue
        video_vec_list = []
        for vid in related_video:
            video_vec_list.append(video_dict[vid]['vec'])
#        scores = cosine_similarity([array['vec']], video_vec_list)
        scores = euclidean_distance([array['vec']], video_vec_list)
        distance_dict = {}
        for index, vid in enumerate(related_video):
            score = scores[0][index]
            if score > 3.0:
                continue
            distance_dict[vid] = score
        if len(distance_dict) == 0:
            continue
        index_str = docid + '\t'
        fw_log.write(docid + '\t' + doc_dict[docid]['title'] + '\n')
#        sort_distance_dict = sorted(distance_dict.iteritems(), key=lambda d:d[1], reverse = True)
        sort_distance_dict = sorted(distance_dict.iteritems(), key=lambda d:d[1])
        str_list = []
        for index, t in enumerate(sort_distance_dict):
            if index < 40:
                vid = t[0]
                score = t[1]
                str_list.append(vid + '\001' + str(score))
                fw_log.write('----------' + vid + '\t' + str(score) + '\t' + video_dict[vid]['title'] + '\n')
        index_str += '\002'.join(str_list)
        fw_index.write(index_str + '\n')
    fw_log.close()
    fw_index.close()
    print index_filepath

if __name__=='__main__':
    main()
