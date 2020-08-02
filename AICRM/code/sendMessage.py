# -*- coding: UTF-8 -*-

import requests
import urllib
def sms_send_bulk(username,password,dstaddr,smbody, dlvtime):   # 帳號/密碼/手機號碼(List)/簡訊內容/預約時間(小時)
    host = "http://smexpress.mitake.com.tw:9600/api/mtk/SmSendPost.asp?username=24697268A&password=52613000&encoding=UTF-8"
    dlvtime = str(int(dlvtime)*60*60)
    count = len(dstaddr)
    msgidList = {}
    msg = ''
    for i in range(count):

        if str(dstaddr[i])[0] == '0':
            msg = msg + "["+str(dstaddr[i])+"]\ndstaddr="+str(dstaddr[i])+"\nsmbody="+smbody[i]+"\n"
        else:
            msg = msg + "[0"+str(dstaddr[i])+"]\ndstaddr=0"+str(dstaddr[i])+"\nsmbody="+smbody[i]+"\n"
        msg = msg + "dlvtime="+dlvtime+"\n"

    r = (requests.post(host, data=msg)).text
    for j in range(count):
        msgid = r
        try:
            msgid = r.split(str(dstaddr[j])+"]\r\nmsgid=")[1].split('\r\n')[0]
            if len(msgid)!=10:
                msgid = r.split(str(dstaddr[j])+"]")[1].split('[')[0]
        except:
            msgid = '-'

        msgidList[dstaddr[j]] = msgid

    return msgidList

# 寄送簡訊(不做預約)
def sendFunction(cell, message):
    msgidList = sms_send_bulk(username="24697268A",password="52613000",dstaddr=cell,smbody=message, dlvtime=0)
    return msgidList

# 寄送簡訊(預約時間)
def sendFunction_batch(cell, message, dlvtime=0):
    msgidList = sms_send_bulk(username="24697268A",password="52613000",dstaddr=cell,smbody=message, dlvtime=dlvtime)
    return msgidList