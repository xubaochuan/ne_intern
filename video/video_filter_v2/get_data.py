#coding=utf-8
import urllib
import json

def main():
    vid_list = load_vid()
    url = "http://nc.inter.m.163.com/nc/rec/getContnetById.html?id="
    for vid in vid_list:
        vurl = url + vid
        f = urllib.urlopen(vurl)
        s = f.read()
        v_dict = json.loads(s)
        if 'mp4_url' in v_dict:
            print vid, v_dict['mp4_url']
        else:
            print vid, 'none url'

def load_vid(filepath = 'vid.csv'):
    fr = open(filepath)
    vid_list = []
    for line in fr.readlines():
        array = line.strip().split(',')
        if ',' not in line or len(array) != 2:
            continue
        vid_list.append(array[0])
        vid_list.append(array[1])
    fr.close()
    return vid_list

if __name__=='__main__':
    main()
