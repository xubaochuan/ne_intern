#! /usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import json
import utility
import time
import os
from logger  import *


class Classifier(multiprocessing.Process):
    def __init__(self, queue, res_dict, res_queue_offline):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.res_dict = res_dict
        self.res_queue_offline = res_queue_offline

    def run(self):
        while True:
            if not self.queue.empty():
                
                try:
                    queue_size = self.queue.qsize()
                    logService.info("queue size is :%d", queue_size)

                    task = self.queue.get(1)
                    rvideoid, vtitle, vurl, offline = task
                except:
                    continue
                res_value = None
                try:
                    print "start process vid:" + rvideoid 
                    result = utility.detect(rvideoid, vurl, vtitle)
                    print "process finished vid:" + rvideoid 
                    now_timestamp = time.time()
                    if result['code'] == 200:
                        if result['unique'] == 1:
                            res_value = (False, "", 0, now_timestamp)
                            logService.info("unique video\tvid:%s\tvurl:%s\tvtitle:%s", rvideoid, vurl, vtitle)
                        else:
                            res_value = (True, result['similar_rvideoid'], 0, now_timestamp)
                            logService.info("repetitive video\tvid:%s\tvurl:%s\tvtitle:%s\tsame_videos:%s", rvideoid, vurl, vtitle, result['similar_rvideoid'])
                    else:
                        logWarning.warning("get same video failed,vid:%s\tvurl:%s\tvtitle:%s,reason:%s", rvideoid, vurl, vtitle, result["msg"])
                except Exception,e:
                    logWarning.warning("get same video code is wrong,vid:%s\tvurl:%s\tvtitle:%s", rvideoid, vurl, vtitle)
                if not res_value:
                    res_value = (False, "", 1, now_timestamp)
                if not offline:
                    self.res_dict[rvideoid] = res_value
                    print self.res_dict
                else:
                    try:
                        self.res_queue_offline.put(res_value)
                        print self.res_queue_offline
                    except Exception as e:
                        msg = str(traceback.format_exc())
                        logWarning.warning("put results to offline queue failed,reason:%s", msg)
            else:
                time.sleep(0.5)

