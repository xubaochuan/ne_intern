#!/usr/bin/python  
# -*- conding:utf-8 -*-  
import os  
from bottle import * 
import urllib
import thread
import json
import video_classify

video_temp = "temp/video"

@route('/nsfw/videourls', methods=['GET', 'POST'])                    
def video_urls():
    urlstrings = request.query.urls.encode("utf-8")
    url_list = urlstrings.split(',')
    if len(url_list) > 0:
        conclusion = judge(url_list)
        data = {'code':200,'msg':'success','data':conclusion}
        return json.dumps(data)
    else:
        data = {'code':400, 'msg':'params error'}
        return json.dumps(data)                                    

def judge(url_list):
    video_dict = {}
    for url in url_list:
        video_name = url.split('/')[-1]
        video_path = os.path.join(video_temp, video_name)
        urllib.urlretrieve(url, video_path)
        video_dict[video_name] = url
    conclusion = video_classify.main(video_dict)
    return conclusion

run(host='0.0.0.0', port=8080) 
