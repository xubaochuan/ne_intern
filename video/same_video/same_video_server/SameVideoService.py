#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import threading
import sys
sys.path.append('./common-gen-py/')
reload(sys)
sys.setdefaultencoding('utf-8')
import pickle
import numpy as np
import json
import traceback
import time
import datetime
import pdb
import string
import threading
import ConfigParser
import socket
import redis
import os
import Judger

#create log directory
log_path = os.path.abspath(os.curdir) + '/logs'
if not os.path.exists(log_path):
    os.makedirs(log_path)

#common thrift gen-py
from rec import SameVideoJudgeService
from rec.ttypes import *

#local direcotry
from logger  import *

#thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.server import TProcessPoolServer
from thrift.server import TNonblockingServer


global queue
global res_dict
global res_queue_offline
global queue_size
global offline_rediscli
offline_rediscli = redis.Redis(host='localhost', port=11103, db=0) 
ports = list()
num_process = 24
queue_size = 10000
queue = multiprocessing.Queue(queue_size)
res_dict = multiprocessing.Manager().dict()
res_queue_offline = multiprocessing.Manager().Queue(queue_size)


class SameVideoHandler:
    
    def __init__(self):
        global res_dict
        global queue
        global queue_size
        global res_queue_offline
        logService.info("init starting")
        self.res_dict = res_dict
        self.queue = queue
        self.queue_size = queue_size
        self.res_queue_offline = res_queue_offline
        print 'init starting'


        logService.debug( ISOTIMEFORMAT, time.localtime() )
        print time.localtime()
        logService.info('init finished.')
    
    def getHealthStatus(self):
        if True:
            return 1;
        else:
            return 0;

    def SameVideo(self, request):
        t_start = datetime.datetime.now()
        response = None
        offline = False
        vid = request.vid
        title = request.title
        video_url = request.video_url
        start_time = datetime.datetime.now()
        if self.queue.qsize() == self.queue_size:
            response = SameVideoResponse(False, "", False)
        else:
            self.queue.put((vid, title, video_url, offline))
            count = 0
            while count < 600:
                count += 1
                if vid in self.res_dict:
                    has_same_video, same_video, precess_successful, _ = self.res_dict[vid]
                    response = SameVideoResponse(has_same_video, same_video, precess_successful)
                    del self.res_dict[vid]
                    break
                time.sleep(0.5)
            if not response:
                response = SameVideoResponse(False, "", 1) 


        end_time = datetime.datetime.now()
        logService.info("time_dis: %s", end_time - start_time)
        logService.info("res dict size: %d", len(self.res_dict))
   
        return response
    def SameVideoOffline(self, requests):
        t_start = datetime.datetime.now()
        offline = True
        for request in requests:
            vid = request.vid
            title = request.title
            video_url = request.video_url
            start_time = datetime.datetime.now()
            if self.queue.qsize() == self.queue_size:
                return False
            else:
                self.queue.put((vid, title, video_url, offline))
        end_time = datetime.datetime.now()
        logService.info("time_dis_offline: %s", end_time - start_time)
        logService.info("res queue size: %d", self.res_queue_offline.qsize())
        return True

def IsPortOK(port):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(1)
    try:
        logService.info('test port %d', port)
        sk.connect(('localhost', port))
        logService.info('port %d is used', port)

        sk.close()
        return False
    except Exception as e:
        logService.info('port %d is ok', port)
        return True

def getPort():
    for port in ports:
        if IsPortOK(port):
            return port
    return None

def hasValidPort():
    if getPort() == None:
        return False;
    return True;

def readConf():
    global ports
    global thread_num

    try:
        conf_file = './conf/same_video.conf'
        conf = ConfigParser.ConfigParser()
        conf.read(conf_file)
        port_str = conf.get("server", "port") 
        thread_num = conf.getint("server", "thread_num") 
        ports = eval(port_str)

        return True
    except Exception as e:
        logError.error(str(e))
        return False

def run():

    if not readConf():
        logService.info('read conf file is failed!')
        #print 'read conf file is failed!'
        return None

    # build news_infer_server
    if not hasValidPort():
        logService.info("doesn't have valid port")
        #print "doesn't have valid port"
        return None

    handler = SameVideoHandler()

    valid_port = getPort()
    if valid_port == None:
        logService.info("doesn't have valid port")
        #print "doesn't have valid port"
        return None

    transport = TSocket.TServerSocket(port=valid_port)
    processor = SameVideoJudgeService.Processor(handler)
    #tfactory = TTransport.TBufferedTransportFactory()
    tfactory = TTransport.TFramedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    
    #server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    #server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    #server = TProcessPoolServer.TProcessPoolServer(processor, transport, tfactory, pfactory)
    #server = TNonblockingServer.TNonblockingServer(processor, transport, tfactory, pfactory)
    server = TNonblockingServer.TNonblockingServer(processor, transport, pfactory)
    server.daemon = True
    server.setNumThreads(thread_num)
    #server.setNumWorkers(thread_num)

    print threading.current_thread()

    print('Starting the infer server...')
    server.serve()
    #logAll.error('done.')
    print('done')

def clean_dict(res_dict):
    while True:
        for key in dict(res_dict):
            _, _, _, time_stamps = res_dict[key]
            now_timestamp = time.time()
            if now_timestamp - time_stamps > 360:
                del res_dict[key]
        time.sleep(100)

def put_res_queue_offline_to_redis(res_queue_offline, offline_rediscli):
    while True:
        now_time_stamp = int(time.time())
        #if now_time_stamp % (60 * 60) == 0:
        if now_time_stamp % (10) == 0 and res_queue_offline.qsize() > 0:
            res = []
            while True:
                if res_queue_offline.qsize() <= 0:
                    break
                (has_same_video, same_video, precess_successful, _), vid = res_queue_offline.get(1)
                temp_res = dict()
                temp_res["vid"] = vid
                temp_res["has_same_video"] = has_same_video
                temp_res["same_video"] = same_video
                temp_res["err_code"] = precess_successful
                logService.info("OFFLINE result\tvid:%s\thas_same_video:%s\tsame_video:%s\terr_code:%s", vid, has_same_video, same_video, precess_successful)
                res.append(temp_res)
            res_str = json.dumps(res)
            key = "SVO_" + str(now_time_stamp)
            print "--------put to redis, key is " + key
            offline_rediscli.set(key, res_str)

        else:
            time.sleep(0.37)




if __name__ == '__main__':
    clean_dict_thread = threading.Thread(target=clean_dict, args=(res_dict,))    
    clean_dict_thread.setDaemon(True)
    clean_dict_thread.start()

    put_res_queue_offline_to_redis_thread = threading.Thread(target = put_res_queue_offline_to_redis, args = (res_queue_offline, offline_rediscli,))
    put_res_queue_offline_to_redis_thread.setDaemon(True)
    put_res_queue_offline_to_redis_thread.start()


    processed = []
    for i in range(num_process):
        processed.append(Judger.Classifier(queue, res_dict, res_queue_offline))

    for i in range(len(processed)):
        processed[i].start()
    run()
