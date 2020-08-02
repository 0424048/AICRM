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
key_file_locations = ['google_key.json', 'google_key_777777.json']

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

    if accounts.get('items'):
        # Get the first Google Analytics account.
        account = accounts.get('items')[0].get('id')

        # Get a list of all the properties for the first account.
        properties = service.management().webproperties().list(
                accountId=account).execute()

        if properties.get('items'):
            # Get the first property id.
            property = properties.get('items')[0].get('id')

            # Get a list of all views (profiles) for the first property.
            profiles = service.management().profiles().list(
                    accountId=account,
                    webPropertyId=property).execute()

            if profiles.get('items'):
                # return the first view (profile) id.
                return profiles.get('items')[0].get('id')

    return None


def get_results(service, profile_id, GAtype):
    # Use the Analytics Service Object to query the Core Reporting API
    # for the number of sessions within the past seven days.

    # 分為split(搜尋key帳號資料下全部GA資訊，分別印出)/all(搜尋key帳號資料下全部GA資訊總計)/ByCampaign(依照Campaign去篩選GA資料)
#    if GAtype == 'split':
#        return service.data().ga().get(
#                ids='ga:' + profile_id,
#                start_date='2018-01-01',
#                end_date='today',
#                metrics='ga:users,ga:visits,ga:goalConversionRateAll,ga:goalCompletionsAll,ga:transactionRevenue',
#                dimensions='ga:sourceMedium',
#                filters='ga:sourceMedium=@AICRM-'
#                ).execute()

    if 'all-' in GAtype:
        fname = (GAtype.split('-')[1]).split('.')[0]
        return service.data().ga().get(
                ids='ga:' + profile_id,
                start_date='2018-01-01',
                end_date='today',
                metrics='ga:users,ga:visits,ga:goalConversionRateAll,ga:goalCompletionsAll,ga:transactionRevenue',
                filters='ga:sourceMedium=@AICRM-'+ fname
                ).execute()
def print_results(results,GAtype):
    # Print data nicely for the user.
    if results and 'totalsForAllResults' in results:
        if GAtype == 'split':
            # 從 DB 搜尋所有帳號
            print ('utm_source-uuid / utm_medium-date-cell | 使用者數量 | 瀏覽量 | 電子商務轉換率 | 交易次數 | 收益')
            for i in results['totalsForAllResults']:
                print i
            today = dt.date.today()
            for account in json.loads(API.getAccounts()):

                # 從DB搜尋所有已送出簡訊的檔名
                # 以GA抓回資料統計 已購買/點擊未購買/尚未點擊 ，並寫入到原message excel檔案後 - UserLabel欄位
                for sendFiles in json.loads(API.getSendMessageFile(account)):
                    # 建立 accountName_ga.csv 檔案
                    if os.path.isfile('AIexcel/' + account + '_ga.csv'):
                        print account+'_ga.csv'
                        df_ga = pd.read_csv('AIexcel/' + account + '_ga.csv' , sep=',', encoding='utf_8_sig',low_memory=False)
                    ModuleMapping = json.loads(API.getMappingData(Vendor=account, FileName=sendFiles['FileName']))  # 轉換模組
                    df = pd.read_csv('messageExl/' + sendFiles['FileName'], sep=',', encoding='utf_8_sig',low_memory=False)
                    if 'UserLabel' not in df:
                        df['UserLabel']  = u'尚未點擊'
                    # try:
                    #     df['UserLabel']  = df['UserLabel'].astype(str).str.replace(u'0', u'尚未點擊')
                    # except:
                    #     print('pass')
                    ClickButNotBuy = [x[0].split(' / ')[1].split('-')[-1] for x in results['rows'] if x[0].split(' / ')[0].split('-')[1] == sendFiles['FileName'].replace(".csv","") and x[5]=='0.0']
                    # print 'ClickButNotBuy:', ClickButNotBuy
                    df.loc[df[ModuleMapping[u'收件人手機']].isin(ClickButNotBuy), 'UserLabel'] = u'點擊未購買'
                    ClickAndBuy = [{x[0].split(' / ')[1].split('-')[-1]:x[5]} for x in results['rows'] if x[0].split(' / ')[0].split('-')[1] == sendFiles['FileName'].replace(".csv","") and x[5]!='0.0']
                    # print 'Buy:',ClickAndBuy
                    for i in ClickAndBuy:
                        df.loc[df[ModuleMapping[u'收件人手機']].astype(str)==str(i.items()[0][0]), 'UserLabel'] = str(i.items()[0][1])
                    df['UserLabel'] = df['UserLabel'].fillna(u'尚未點擊')
                    df.to_csv('messageExl/' + sendFiles['FileName'], sep=',', encoding='utf-8',index=0)
                    df = df[[ModuleMapping[u'收件人手機'],'UserLabel']]
                    df.rename(columns={ModuleMapping[u'收件人手機']:u'收件人手機'}, inplace=True)

                    if os.path.isfile('AIexcel/' + account + '_ga.csv'):
                        res = pd.concat([df_ga, df],axis=0, sort=False).drop_duplicates(subset=u'收件人手機', keep='last').reset_index(drop=True)
                        if 'next_time' in res:
                            res['next_time'] = res['next_time'].fillna(today+pd.DateOffset(days=10))
                        else:
                            res['next_time'] = today+pd.DateOffset(days=10)

                        res.to_csv('AIexcel/'+ account + '_ga.csv', sep=',', encoding='utf_8_sig',index=0)
                    else:
                        df.to_csv('AIexcel/' + account + '_ga.csv', sep=',', encoding='utf_8_sig',index=0)
                        res = df

        if 'all-' in GAtype:
            print results
            print '檔名:', GAtype.split('-')[1],'使用者數量:',results['rows'][0][0], '瀏覽量:',results['rows'][0][1], '電子商務轉換率:',results['rows'][0][2], '交易次數:',results['rows'][0][3], '收益:',results['rows'][0][4]
            API.changeSendMessageResult_GA(fname = GAtype.split('-')[1], GA_Click= results['rows'][0][1], GA_TransactionTimes= results['rows'][0][2], GA_Revenue = results['rows'][0][4])
        if 'ByCampaign' in GAtype:
            print results['rows']
    else:
        pass
        # print results


    # if results:
    #     print 'View (Profile):', results.get('profileInfo').get('profileName')
    #     print 'Total Sessions:', results.get('rows')[0][0]

    # else:
    #     print 'No results found'

def main():
    print('HI')
    # Define the auth scopes to request.
    scope = 'https://www.googleapis.com/auth/analytics.readonly'
    for key_file_location in key_file_locations:
        print(key_file_location)
        # Authenticate and construct service.
        service = get_service(
                api_name='analytics',
                api_version='v3',
                scopes=[scope],
                key_file_location='key/'+key_file_location)
        print("HI2")
        profile_id = get_first_profile_id(service)
        #print_results(get_results(service, profile_id, 'split'),'split')
        for account in json.loads(API.getAccounts()):
            for sendFiles in json.loads(API.getSendMessageResult(account)):
                # 紀錄GA資訊
                print sendFiles
                print_results(get_results(service, profile_id, 'all-' +sendFiles['FileName']),'all-'+sendFiles['FileName'])
                # 從三竹網站GET紀錄簡訊發送狀態資訊
                if os.path.isfile('messageExl/' + sendFiles['FileName']):
                    df = pd.read_csv('messageExl/' + sendFiles['FileName'] , sep=',', encoding='utf_8_sig',low_memory=False)
                    counter_finish = 0
                    counter_reservation = 0
                    counter_timeout = 0
                    counter_error = 0
                    if 'msgid' in df:
                        for msgid in df['msgid']:
                            url = 'http://smexpress.mitake.com.tw:9600/api/mtk/SmQueryGet.asp?username=24697268A&password=52613000&msgid=' + str(msgid)
                            r = requests.get(url).text
                            try:
                                if r.split('\t')[1]=='1' or r.split('\t')[1]=='2' or r.split('\t')[1]=='4':
                                    counter_finish+=1
                                elif r.split('\t')[1]=='0':
                                    counter_reservation+=1
                                elif r.split('\t')[1]=='8':
                                    counter_timeout+=1
                                else :
                                    counter_error+=1
                            except:
                                pass
                        # 記錄到 DB
                        print('FileName', 'counter_finish', 'counter_reservation', 'counter_timeout', 'counter_error')
                        print(sendFiles['FileName'], counter_finish, counter_reservation, counter_timeout, counter_error)
                        API.changeSendMessageResult_message(fname = sendFiles['FileName'], MessageStatus_finish= counter_finish, MessageStatus_reservation= counter_reservation, MessageStatus_timeout = counter_timeout, MessageStatus_error=counter_error)

if __name__ == '__main__':
    main()