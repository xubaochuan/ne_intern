#!/usr/bin/python  
# -*- conding:utf-8 -*-  
import os  
from bottle import * 
import urllib
import urllib2
import threading
import thread
import json
import time
import video_classify

video_temp = "temp/video"
log_dir = "log"

@route('/nsfw/videourls', methods=['GET', 'POST'])                    
def video_urls():
    url_strings = request.query.urls.encode("utf-8")
    recall_url = request.query.recall.encode("utf-8")
    
    write_log('request', recall_url + ' ' + url_strings)
    
    url_list = url_strings.split(',')
    if len(url_list) > 0:
#        nsfw_judge = threading.Thread(target=judge,args=(url_list))
#        nsfw_judge.setDaemon(True)
#        nsfw_judge.start()
        thread.start_new_thread(judge,(url_list,recall_url,))
        data = {'code':200,'msg':'start process'}
        return json.dumps(data)
    else:
        data = {'code':400, 'msg':'params error'}
        return json.dumps(data)                                    

def judge(url_list,recall_url):
    video_dict = {}
    for url in url_list:
        video_name = url.split('/')[-1]
        video_path = os.path.join(video_temp, video_name)
        urllib.urlretrieve(url, video_path)
        video_dict[video_name] = url
    conclusion = video_classify.main(video_dict)
    postdata = dict(code=200,msg='success',jsonResult=json.dumps(conclusion))
    response = post(recall_url, postdata)
    write_log('post', recall_url + ' ' + json.dumps(conclusion))
    print response
    
def write_log(op_type, content):
    today = time.strftime('%Y%m%d',time.localtime(time.time()))
    log_filename = today + '.log'
    log_path = os.path.join(log_dir, log_filename)
    log = open(log_path, 'a')
    current = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    log.write(current + ' ' + op_type + ' ' + content + '\n')
    log.close()

def post(url, data): 
    req = urllib2.Request(url) 
    data = urllib.urlencode(data) 
    #enable cookie 
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) 
    response = opener.open(req, data) 
    return response.read()

run(host='0.0.0.0', port=8080) 

