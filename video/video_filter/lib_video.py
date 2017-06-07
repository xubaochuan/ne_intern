#coding=utf-8
import multiprocessing
import time
import utility
import urllib
import os

log_dir = 'log/offline/'

def write_log(log_type, rvideoid, vurl, vtitle, msg =''):
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

class Producer(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.index = 166685
        fr = open('video0308_filter.txt')
        self.lib_data = fr.readlines()
        self.max_video = len(self.lib_data)

    def run(self):
        while True:
            second = time.strftime('%S',time.localtime(time.time()))
            if second == '30':
                current = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                queue_size = self.queue.qsize()
                queue_log(current, queue_size)

            if self.queue.qsize() < 500:
                if self.index < self.max_video:
                    video_info = self.lib_data[self.index]
                    self.index += 1
                    queue.put(video_info)
                else:
                    print 'done'
                    time.sleep(5)
            else:
                time.sleep(1)

class Consumer(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            if not self.queue.empty():
                try:
                    task = self.queue.get(1)
                    task_list = task.strip().split(',')
                    if ',' not in task or len(task_list) != 5:
                        continue
                    rvideoid = task_list[0]
                    vtitle = task_list[1]
                    vurl = task_list[2]
                except Exception,e:
                    continue
                try:
                    result = utility.detect(rvideoid, vurl, vtitle)
                    if result['code'] == 200:
                        if result['unique'] == 1:
                            write_log('unique', rvideoid, vurl, vtitle, 'unique')
                        else:
                            write_log('repetitive', rvideoid, vurl ,vtitle, result['similar_rvideoid'])
                    else:
                        write_log('exception', rvideoid, vurl, vtitle, result['msg'])
                except Exception,e:
                    try:
                        write_log('exception', rvideoid, vurl, vtitle, str(e))
                    except:
                        pass
            else:
                time.sleep(1)
                print 'consumer sleep'

queue_size = 1000
queue = multiprocessing.Queue(queue_size)
num_process = 10
process_list = []

video_producer = Producer(queue)

video_producer.start()

time.sleep(2)

for i in range(num_process):
    process_list.append(Consumer(queue))

for i in range(num_process):
    process_list[i].start()

for i in range(len(process_list)):
    process_list[i].join()
