############################################################
#                                                          #
#                          hprose                          #
#                                                          #
# Official WebSite: http://www.hprose.com/                 #
#                   http://www.hprose.org/                 #
#                                                          #
############################################################

############################################################
#                                                          #
# hprose/common.py                                         #
#                                                          #
# hprose common for python 3.0+                            #
#                                                          #
# LastModified: Apr 12, 2014                               #
# Author: Ma Bingyao <andot@hprose.com>                    #
#                                                          #
############################################################

class HproseResultMode:
    Normal = 0
    Serialized = 1
    Raw = 2
    RawWithEndTag = 3


class HproseException(Exception):
    pass


class NetErrorException(HproseException):
    """网络异常，数据没有发送到服务方"""
    pass


class ServiceException(HproseException):
    """通讯成功，服务方主动抛出的异常"""
    pass


class HproseFilter(object):
    def inputFilter(self, data, context):
        return data

    def outputFilter(self, data, context):
        return data
