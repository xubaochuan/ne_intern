#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging, logging.handlers

def getLogger(loggerName , loggerLevel , loggerLocation ):
    logger = logging.getLogger(loggerName)
    logger.setLevel(loggerLevel)
    format = "%(asctime)s %(levelname)s %(message)s"
    formater = logging.Formatter(format)
    handler = logging.handlers.TimedRotatingFileHandler(loggerLocation, "D", 1, 10)
#    handler.suffix = "%Y%m%d.%H:%M:%S"
    handler.setFormatter(formater)
    logger.addHandler(handler)

    return logger

#---------------Service log setting start---------------#

# 服务日志
logService = getLogger('logService' , logging.INFO , 'logs/service.log')
#logService = getLogger('logService' , logging.WARNING, 'log1/service.log')
# 输出未解析成功日志
logDocNoInfer =  getLogger('docNoInfer' , logging.INFO , 'logs/docNoInfer.log')
# 异常数据的日志
logException = getLogger('logException', logging.INFO, 'logs/exception.log')
# 服务入参的日志
logArgs = getLogger('logArgs', logging.INFO, 'logs/args.log')

# 服务入参的日志
logWarning = getLogger('logWarning', logging.WARNING, 'logs/warning.log')
#logWarning = getLogger('logWarning', logging.WARNING, 'log1/warning.log')
# 服务入参的日志
logError = getLogger('logError', logging.ERROR, 'logs/error.log')


ISOTIMEFORMAT='%Y-%m-%d %X'

#---------------Service log setting end---------------#


