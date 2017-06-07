#coding=utf-8
import multiprocessing
import time
import utility
import urllib
import os
import signal

log_dir = 'log/offline/'
runtime_limit = 300

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

def handle(signum, frame):
    raise RuntimeError('run time out')

class Producer(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.index = 0
#        fr = open('video0308_filter.txt')
        fr = open('vids')
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
                    queue.put_nowait(video_info)
                else:
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
                    task = self.queue.get_nowait()
                    if task == None:
                        continue
                    task_list = task.strip().split(' ')
                    if ' ' not in task or len(task_list) != 2:
                        continue
                    rvideoid = task_list[0]
                    vtitle = 'none'
                    vurl = task_list[1]
                except Exception,e:
                    continue
                try:
                    signal.signal(signal.SIGALRM, handle)
                    signal.alarm(runtime_limit)
                    result = utility.detect(rvideoid, vurl, vtitle)
                    signal.alarm(0)

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
