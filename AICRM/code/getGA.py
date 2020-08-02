# -*- coding: utf-8 -*-
"""A simple example of how to access the Google Analytics API."""

from apiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import os
import API
import xlrd
import json
import pandas as pd
# df = pd.read_csv('AIexcel/666666_ga.csv' , sep=',', encoding='utf_8_sig',low_memory=False)
import numbers
import requests
import datetime as dt
import time
import numpy as np
key_file_locations = ['google_key.json','google_key_777777.json']

PATH  = '/home/ec2-user/excel/'
def get_service(api_name, api_version, scopes, key_file_location):
    """Get a service that communicates to a Google API.

    Args:
        api_name: The name of the api to connect to.
        api_version: The api version to connect to.
        scopes: A list auth scopes to authorize for the application.
        key_file_location: The path to a valid service account JSON key file.

    Returns:
        A service that is connected to the specified API.
    """
    credentials = Credentials.from_service_account_file(
            key_file_location, scopes=scopes)
    # credentials = ServiceAccountCredentials.from_json_keyfile_name(
    #         key_file_location, scopes=scopes)

    # Build the service object.
    service = build(api_name, api_version, credentials=credentials)

    return service


def get_first_profile_id(service):
    # Use the Analytics service object to get the first profile id.

    # Get a list of all Google Analytics accounts for this user
    accounts = service.management().accounts().list().execute()
    acclist = []

    if accounts.get('items'):
        # Get the first Google Analytics account.
        account = accounts.get('items')[0].get('id')

        # Get a list of all the properties for the first account.
        properties = service.management().webproperties().list(
                accountId=account).execute()

        if properties.get('items'):
            # Get the first property id.
            acclist =[]
            for i in range(len(properties.get('items'))):
                property = properties.get('items')[i].get('id')

                # Get a list of all views (profiles) for the first property.
                profiles = service.management().profiles().list(
                        accountId=account,
                        webPropertyId=property).execute()

                if profiles.get('items'):
                    # return the first view (profile) id.
                    acclist.append(profiles.get('items')[0].get('id'))

            return acclist

    return None


def get_results(service, profile_id, GAtype):
    # Use the Analytics Service Object to query the Core Reporting API
    # for the number of sessions within the past seven days.

    # 分為split(搜尋key帳號資料下全部GA資訊，分別印出)/all(搜尋key帳號資料下全部GA資訊總計)/ByCampaign(依照Campaign去篩選GA資料)
    if GAtype == 'split':
        return service.data().ga().get(
               ids='ga:' + profile_id,
               start_date='2018-01-01',
               end_date='today',
               metrics='ga:users,ga:visits,ga:goalConversionRateAll,ga:transactions,ga:transactionRevenue',
               dimensions='ga:sourceMedium',
               filters='ga:sourceMedium=@AICRM-'
               ).execute()

    elif 'all-' in GAtype:
        fname = (GAtype.split('-')[1]).split('.')[0]
        return service.data().ga().get(
                ids='ga:' + profile_id,
                start_date='2018-01-01',
                end_date='today',
                metrics='ga:users,ga:visits,ga:goalConversionRateAll,ga:transactions,ga:transactionRevenue',
                filters='ga:sourceMedium=@AICRM-'+ fname
                ).execute()
def print_results(results,GAtype):
    # Print data nicely for the user.
    #print('View (Profile):', results.get('profileInfo').get('profileName'))
    #print('Total Sessions:', results.get('rows')[0][0])
    if results and 'rows' in results:
        if GAtype == 'split':
            print('split')
            # 從 DB 搜尋所有帳號
            print ('utm_source-uuid / utm_medium-date-cell | 使用者數量 | 瀏覽量 | 電子商務轉換率 | 交易次數 | 收益')
            for i in results['rows']:
                print i
            today = dt.date.today()
            for account in json.loads(API.getAccounts()):

                # 從DB搜尋所有已送出簡訊的檔名
                # 以GA抓回資料統計 已購買/點擊未購買/尚未點擊 ，並寫入到原message excel檔案後 - UserLabel欄位
                for sendFiles in json.loads(API.getSendMessageResultAll(account)):
                    # 建立 accountName_ga.csv 檔案
                    if os.path.isfile(PATH +'AIexcel/' + account + '_ga.csv'):
                        df_ga = pd.read_csv(PATH +'AIexcel/' + account + '_ga.csv' , sep=',', encoding='utf_8_sig',low_memory=False)
                    ModuleMapping = json.loads(API.getMappingData(Vendor=account, FileName=sendFiles['FileName']))  # 轉換模組
                    if os.path.isfile(PATH +'messageExl/' + sendFiles['FileName']):
                        df = pd.read_csv(PATH +'messageExl/' + sendFiles['FileName'], sep=',', encoding='utf_8_sig',low_memory=False)
                        dfList = df[ModuleMapping[u'收件人手機']].values
                        if 'UserLabel' not in df:
                            df['UserLabel']  = u'尚未點擊'

                        if 'MessageFile' in sendFiles:
                            if  sendFiles['MessageFile'] == None:
                                continue
                        else:
                            continue

                        ClickButNotBuy = [x[0].split(' / ')[1].split('-')[-1] for x in results['rows'] if x[0].split(' / ')[0].split('-')[1] == sendFiles['MessageFile'].replace(".csv","") and x[5]=='0.0']
                        # print 'ClickButNotBuy:', ClickButNotBuy
                        df.loc[df[ModuleMapping[u'收件人手機']].isin(ClickButNotBuy), 'UserLabel'] = u'點擊未購買'
                        ClickAndBuy = [{x[0].split(' / ')[1].split('-')[-1]:x[5]} for x in results['rows'] if x[0].split(' / ')[0].split('-')[1] == sendFiles['MessageFile'].replace(".csv","") and x[5]!='0.0']
                        # print 'Buy:',ClickAndBuy
                        GA_Revenue = 0

                        for i in ClickAndBuy:
                            if float(i.items()[0][0]) in dfList or str(int(i.items()[0][0])) in dfList or str((i.items()[0][0])) in dfList:
                                df.loc[df[ModuleMapping[u'收件人手機']].astype(str)==str(i.items()[0][0]), 'UserLabel'] = str(i.items()[0][1])

                        df['UserLabel'] = df['UserLabel'].fillna(u'尚未點擊')
                        df.to_csv(PATH +'messageExl/' + sendFiles['FileName'], sep=',', encoding='utf-8',index=0)
                        df = df[[ModuleMapping[u'收件人手機'],'UserLabel']]
                        df.rename(columns={ModuleMapping[u'收件人手機']:u'收件人手機'}, inplace=True)

                        dfUserLabel = df['UserLabel'].values
                        GA_Click = np.count_nonzero(dfUserLabel == u'點擊未購買')
                        GA_NotClick = np.count_nonzero(dfUserLabel == u'尚未點擊')
                        GA_TransactionTimes = len(pd.to_numeric(df['UserLabel'], errors='coerce').dropna())
                        GA_Revenue = int(pd.to_numeric(df['UserLabel'], errors='coerce').sum())
                        try:
                            print('changeSendMessageResult_GA:', sendFiles['FileName'], GA_Click, GA_TransactionTimes,GA_Revenue)
                            API.changeSendMessageResult_GA(fname = sendFiles['FileName'], GA_Click= GA_Click, GA_TransactionTimes= GA_TransactionTimes, GA_Revenue = GA_Revenue)
                        except:
                            print('#ERR#changeSendMessageResult_GA:', sendFiles['FileName'], GA_Click, GA_TransactionTimes,GA_Revenue)
                            pass
                        if os.path.isfile(PATH +'AIexcel/' + account + '_ga.csv'):
                            res = pd.concat([df_ga, df],axis=0, sort=False).drop_duplicates(subset=u'收件人手機', keep='last').reset_index(drop=True)
                            res[u'收件人手機'] = res[u'收件人手機'].astype(dtype=np.int64,errors = 'ignore')
                            if 'next_time' in res:
                                res['next_time'] = res['next_time'].fillna(today+pd.DateOffset(days=10))
                            res.to_csv(PATH +'AIexcel/'+ account + '_ga.csv', sep=',', encoding='utf_8_sig',index=0)
                        else:
                            df[u'收件人手機'] = df[u'收件人手機'].astype(dtype=np.int64,errors = 'ignore')
                            if 'next_time' in df:
                                df['next_time'] = df['next_time'].fillna(today+pd.DateOffset(days=10))
                            df.to_csv(PATH +'AIexcel/' + account + '_ga.csv', sep=',', encoding='utf_8_sig',index=0)
        elif 'all-' in GAtype:
            print '檔名:', GAtype.split('-')[1],'使用者數量:',results['rows'][0][0], '瀏覽量:',results['rows'][0][1], '電子商務轉換率:',results['rows'][0][2], '交易次數:',results['rows'][0][3], '收益:',results['rows'][0][4]
            API.changeSendMessageResult_GA(fname = GAtype.split('-')[1], GA_Click= results['rows'][0][1], GA_TransactionTimes= results['rows'][0][2], GA_Revenue = results['rows'][0][4])
        if 'ByCampaign' in GAtype:
            print results['rows']
    else:
        if 'all-' in GAtype:
            print '檔名:', GAtype.split('-')[1],'-還沒有紀錄'
            API.changeSendMessageResult_GA(fname = GAtype.split('-')[1], GA_Click= '0', GA_TransactionTimes= '0', GA_Revenue = '0')

def main():

    # Define the auth scopes to request.
    scope = 'https://www.googleapis.com/auth/analytics.readonly'

    for account in json.loads(API.getAccounts()):
        for sendFiles in json.loads(API.getFiveDaysSendMessageResult(account)):
            # 從三竹網站GET紀錄簡訊發送狀態資訊
            print(u'StartRecordMessage：' , sendFiles['FileName'])
            if os.path.isfile(PATH +'messageExl/' + sendFiles['FileName']):
                df = pd.read_csv(PATH +'messageExl/' + sendFiles['FileName'] , sep=',', encoding='utf_8_sig',low_memory=False)
                counter_finish = 0
                counter_reservation = 0
                counter_timeout = 0
                counter_error = 0
                if 'msgid' in df:
                    for msgid in df['msgid']:
                        url = 'http://smexpress.mitake.com.tw:9600/api/mtk/SmQueryGet.asp?username=24697268A&password=52613000&msgid=' + str(msgid)
                        for i in range(3):
                            r = requests.get(url).text
                            if r :
                                r = r.split('\t')[1]
                                break
                            elif i>=2:
                                r =='err'
                            else:
                                time.sleep(0.1)
                        if r=='1' or r=='2' or r=='4':
                            counter_finish+=1
                        elif r=='0':
                            counter_reservation+=1
                        elif r=='8':
                            counter_timeout+=1
                        else :
                            counter_error+=1

                    # 記錄到 DB
                    print('FileName', 'counter_finish', 'counter_reservation', 'counter_timeout', 'counter_error')
                    print(sendFiles['FileName'], counter_finish, counter_reservation, counter_timeout, counter_error)
                    API.changeSendMessageResult_message(fname = sendFiles['FileName'], MessageStatus_finish= counter_finish, MessageStatus_reservation= counter_reservation, MessageStatus_timeout = counter_timeout, MessageStatus_error=counter_error)


    for key_file_location in key_file_locations:
    #print(key_file_location)
        # Authenticate and construct service.
        service = get_service(
                api_name='analytics',
                api_version='v3',
                scopes=[scope],
                key_file_location=PATH +'key/'+key_file_location)

        profile_id = get_first_profile_id(service)

        for pid in profile_id:
            print_results(get_results(service, pid, 'split'),'split')
            # for account in json.loads(API.getAccounts()):
            #     for sendFiles in json.loads(API.getSendMessageResult(account)):
            #         # 紀錄GA資訊
            #         print_results(get_results(service, pid, 'all-' +sendFiles['FileName']),'all-'+sendFiles['FileName'])


if __name__ == '__main__':
    main()