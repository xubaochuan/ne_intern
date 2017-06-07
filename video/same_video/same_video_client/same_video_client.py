#!/usr/bin.env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('common-gen-py')
reload(sys)
sys.setdefaultencoding('utf-8')


from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from rec import SameVideoJudgeService
from rec.ttypes import *
import urllib2


import json

default_port = 17000
default_ip   = '10.170.164.74'


def conn_try_again(function):
    def wrapped(*args, **kwargs):
        RETRIES = 0
        try:
            return function(*args, **kwargs)
        except Exception, err:
            if RETRIES < 2:
                RETRIES += 1
                return wrapped(*args, **kwargs)               
            else:
                raise Exception(err)
    return wrapped

def run():
    transport = TSocket.TSocket(default_ip, default_port)
    #transport = TTransport.TBufferedTransport(transport)
    transport = TTransport.TFramedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    client = SameVideoJudgeService.Client(protocol)
    transport.open()
    connect = conn_try_again(urllib2.urlopen)

    print '----------------------------------------'

    try:
        print 'test service health status'
        health = client.getHealthStatus()
        if health:
            print 'service is health with status = ' + str(health)
        else:
            print 'service is not health with status = ' + str(health)
    except Thrift.TException as te:
        print 'ERROR: test service health status exception'
        print str(te)
    
    print '----------------------------------------'

    for line in sys.stdin:
        line = line.rstrip("\n")
        items = line.split(" ")
        vid = items[0]
        #title = items[1]
        title = "fdafasfsd"
        video_url = items[1]
        req = SameVideoRequest(vid, title, video_url)
        res = client.SameVideo(req)
        print "%s\t%s\t%s" % (vid, res.has_same_video, res.same_video)


    transport.close()

if __name__ == '__main__':
    run()
    print 'done'
