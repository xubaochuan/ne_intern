#! /usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
from bottle import route,request,run
import json
import utility
import time
import os
import urllib2
import urllib

@route('/video/filter', methods=['GET', 'POST'])
def index():
    rvideoid = request.query.rvideoid.encode("utf-8")
    vurl = request.query.vurl.encode("utf-8")
    vtitle = request.query.vtitle.encode("utf-8")
    recall = request.query.recall.encode("utf-8")

    if rvideoid != '' and vurl != '' and recall != '':
        if queue.qsize() == queue_size:
            data = {'code': 400, 'msg': 'queue is full'}
            return json.dumps(data)
        else:
            queue.put(rvideoid + '&&&' + vurl + '&&&' + vtitle + '&&&' + recall)
            data = {'code': 200, 'msg': 'start process'}
            return json.dumps(data)
    else:
        data = {'code': 400, 'msg': 'params error'}
        return json.dumps(data)

num_process = 24
queue_size = 10000
log_dir = 'log/online/'

def write_log(log_type, rvideoid, vurl, vtitle, msg=''):
    today = time.strftime('%Y%m%d',time.localtime(time.time()))
    log_filename = log_type + '_' + today + '.log'
    log_path = os.path.join(log_dir, log_filename)
    current = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    log = open(log_path, 'a')
    log.write(rvideoid + '\t' + vurl + '\t' + vtitle + '\t' + msg + '\t' + current + "\n")
    log.close()

def queue_log(rtime, count):
    today = time.strftime('%Y%m%d',time.localtime(time.time()))
    log_filename = 'queue_' + today + '.log'
    log_path = os.path.join(log_dir, log_filename)
    log = open(log_path, 'a')
    log.write(rtime + '\t' + str(count) + '\n')
    log.close()

def post_result(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data) 
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) 
    response = opener.open(req, data) 
    return response.read()

class Classifier(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            if not self.queue.empty():
                
                try:
                    current = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                    queue_size = self.queue.qsize()
                    queue_log(current, queue_size)

                    task = self.queue.get(1)
                    rvideoid = task.split('&&&')[0]
                    vurl = task.split('&&&')[1]
                    vtitle = task.split('&&&')[2]
                    recall = task.split('&&&')[3]
                except:
                    continue

                try:
                    result = utility.detect(rvideoid, vurl, vtitle)
                    if result['code'] == 200:
                        if result['unique'] == 1:
                            write_log('unique', rvideoid, vurl, vtitle, 'unique')
                        else:
                            write_log('repetitive', rvideoid, vurl, vtitle, result['similar_rvideoid'])
                    else:
                        write_log('exception', rvideoid, vurl, vtitle, result['msg'])
                    try:
                        post_result(recall, dict(jsonResult=json.dumps(result)))
                    except Exception,e:
                        write_log('recall', rvideoid, vurl, vtitle, str(e))
                except Exception,e:
                    try:
                        write_log('exception', rvideoid, vurl, vtitle, str(e))
                    except:
                        pass
            else:
                time.sleep(0.5)

queue = multiprocessing.Queue(queue_size)
processed = []
for i in range(num_process):
    processed.append(Classifier(queue))

for i in range(len(processed)):
    processed[i].start()

run(host='0.0.0.0', port=18080)

#for i in range(len(processed)):
#   processed[i].join()
