# -*- coding: utf-8 -*-
import pandas as pd
import API
import json
from pyshorteners import Shortener
import os
fileList={}
shortener = Shortener('Tinyurl', timeout=9000)
for account in json.loads(API.getAccounts()):
    for sendFiles in json.loads(API.getSendMessageResult(account)):
        if os.path.isfile('messageExl/' + sendFiles['FileName']):
            df = pd.read_csv('messageExl/' + sendFiles['FileName'] , sep=',', encoding='utf_8_sig',low_memory=False)
            if u'專屬網址' in df:
                try:
                    url = df[u'專屬網址'].values[0]
                    print url
                    longer = shortener.expand(url)
                    fileList[sendFiles['FileName']] = longer.split('AICRM-')[1].split('&')[0] + '.csv'
                except:
                    print sendFiles['FileName']

print(fileList)


for F, m in fileList.items():
    API.Cangeee(F,m)

for key, value in largeSet.items()[1:]:
                       

df = pd.read_csv('0978136278' , sep=',', encoding='utf_8_sig',low_memory=False)
dfList = df[u'收件人手機'].values
ClickAndBuy = {'0986572646':500,'0925232750':300,'0978136278':400}
for key, value in ClickAndBuy.items():
    if key in dfList or int(key) in dfList:
        df.loc[df[u'收件人手機'].astype(str)==str(key), 'UserLabel'] = str(value)
        GA_Revenue = GA_Revenue + int(float(value))


df[u'收件人手機'].astype(str)

df.loc[df[u'收件人手機'].astype(str)==str('A0933963315'), 'UserLabel'] = "尚未"