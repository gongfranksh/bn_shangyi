# -*- coding: utf-8 -*-
import xmlrpclib

#本地环境
HOST='localhost'
PORT = 8069
DB = 'shangyi'
USER = 'admin'
PASS = '..'

#测试环境
#HOST='192.168.168.235'
#PORT = 5069
#DB = 'shangyi'
#USER = 'admin'
#PASS = '..'

#正式环境
#HOST='192.168.168.219'
#PORT = 8069
#DB = 'sycan'
#USER = 'admin'
#PASS = 'buynowsy'

url = 'http://%s:%d/xmlrpc/common' % (HOST , PORT)

sock = xmlrpclib.ServerProxy(url)
uid = sock.login(DB,USER,PASS)

print "UID=%d" % (uid)

urlx = 'http://%s:%d/xmlrpc/object' % (HOST , PORT)
sock = xmlrpclib.ServerProxy(urlx)
dayjob = sock.execute(DB,uid,PASS,'sync.shangyi.data','auto_update',False)
print dayjob