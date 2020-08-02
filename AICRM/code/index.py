# -*- coding: utf-8 -*-
from flask import Flask, request,redirect,url_for,session,render_template, flash
import os, glob
app = Flask(__name__)

from dateutil.parser import parse
import datetime
import numpy as np
import six
import pandas as pd
import xlrd
import sys
import json
from flask import send_from_directory
import uuid
import mimetypes
from time import gmtime, strftime
import time
from datetime import timedelta
import csv
import openpyxl
import codecs
import chardet
import datetime as dt
from pandas import DataFrame
import urllib

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1) # 修改緩存時間，秒做單位
from pyshorteners import Shortener
from threading import Thread

# 資料夾下檔案
# API.py檔案(包含資料庫新增刪除修改資料等functions)
import API
# AI.py檔案(AI篩選functions)
import AI
# sendMessage.py檔案(發送山竹簡訊functions)
import sendMessage
# DataCollection.py檔案(取得資料庫資料functions)
import DataCollection

# tiny縮網址
def tinyURLShortner(baseurl ,MessageContent, inputlist, df, fname):
    from time import gmtime, strftime
    short = Shortener('Tinyurl', timeout=9000)
    outputlist=[]
    contentlist=[]
    k = 0
    ii = 1
    totalCount = 0.0
    totallengh = len(inputlist)
    print(inputlist)
    for url in inputlist:
        try:
            url = baseurl + str(url)
            time1 = dt.datetime.now()
            for i in range(20):
                try:
                    shortenURL=short.short(''.join(url))
                except Exception, e:
                    if i >= 19:
                        print "errrrr:", url
                        shortenURL = url
                    else:
                        print "err:" + str(i)
                        time.sleep(0.5)
                else:
                    time.sleep(0.1)
                    break
            Content = MessageContent + shortenURL
            outputlist.append(shortenURL)
            contentlist.append(Content)
            k = k+1
            totalCount = totalCount+1
            if k == 10:
                p = '{percent:.2%}'.format(percent=totalCount/totallengh)
                print("Created Length:",ii*10)
                time2 = dt.datetime.now()
                print("onece/time:",str((time2 - time1)/10))
                # 動態記錄創建進度%值至DB
                API.changeMessageFileStatus(fname,u'創建中...'+ str(p))
                k = 0
                time1 = dt.datetime.now()
        except:
            pass
    # 將[專屬網址]、[簡訊內容]寫入原簡訊檔案csv
    try:
        df[u'專屬網址'] = outputlist
        df[u'簡訊內容'] = contentlist
    except:
        df[u'專屬網址'] = pd.Series(outputlist)
        df[u'簡訊內容'] = pd.Series(contentlist)
    df.to_csv('messageExl/' +fname, sep=',', encoding='utf_8_sig',index=0)

    # DB.MessageFile 更改簡訊狀態
    API.changeMessageFileStatus(fname,u'建檔完成-'+ strftime("%y%m%d %H:%M:%S", gmtime()))

# 在後台建立線程跑tiny縮網址
def async_function(baseurl ,MessageContent, inputlist, df, fname):
    thr = Thread(target=tinyURLShortner, args=[baseurl, MessageContent, inputlist, df, fname])
    thr.start()
    return thr

# 判斷文字狀態是否為日期格式
def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False

# 以item取得 dictionary 的主鍵key
def key_for_value(d, value):
    for k, v in d.iteritems():
        if v == value:
            return k

# 500 Error 導向上傳檔案頁面
@app.errorhandler(500)
def internal_error(error):
    if not session.get('logged_in'):
        return redirect(url_for('logingpage'))
    return redirect(url_for('uploadExcel'))


# html/python get呼叫用之function
@app.route("/getAPI/<req>/<fname>", methods=['GET'])
def getAPI(req,fname):
    if req == 'getMappingData':         # 取得檔案轉換模組
        return (API.getMappingData(Vendor=session['Vendor'], FileName= fname))
    # 刪除檔案
    if 'deleteFile' in req:
        delete_type = fname.split("-")[0]
        filename = fname.split("-")[1]
        if delete_type == 'UploadFile':
            for filename in glob.glob("uploadExl/" + filename + ".*"):
                os.remove(filename)
            return (API.deleteUploadFile(FileName= filename))
        if delete_type == 'FilterFile':
            for filename in glob.glob("filteredExl/" + filename + ".*"):
                os.remove(filename)
            return (API.deleteFilterFile(FileName= filename))
        if delete_type == 'MessageFile':
            for filename in glob.glob("messageExl/" + filename + "*"):
                os.remove(filename)
            API.deleteMessageResult(FileName= filename)
            return (API.deleteMessageFile(FileName= filename))
        if delete_type == 'AIfilterFile':
            for filename in glob.glob("AIexcel/" + filename + "*"):
                os.remove(filename)
            return (API.deleteAIfilterFile(FileName= filename))

    # 取得檔案中產品名稱List
    if 'getBuyProductList' in req:
        orderType = req.split('-')[1]   # 名單類型
        if orderType =='AIexcel':
            m = {u'收件人手機':u'收件人手機'}
            df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
        elif orderType =='allFile':
            m = {u'收件人手機':u'收件人手機',u'收件人姓名':u'收件人姓名',u'商品名稱':u'商品名稱',u'訂單日期':u'付款日期',u'訂單金額':u'商品總價'}
            df = pd.read_csv('AIexcel/' +fname , sep=',', encoding='utf8',low_memory=False)
        else:
            m = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= fname))
            df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
        if len(m)<1:
            return json.dumps({'NotCreateModule':'NotCreateModule'})
        if orderType !='AIexcel' and (u'商品名稱' in m) and m[u'商品名稱'] in df.columns:
            BuyProductName = (df.drop_duplicates([m[u'商品名稱']]))[m[u'商品名稱']].values.tolist()
            BuyProductName.sort()
            return json.dumps(BuyProductName)
        else:
            return json.dumps({})

# html/python post呼叫用之function
@app.route("/postAPI/<req>", methods=['POST'])
def postAPI(req):
    # 取得已上傳的檔案List
    if req == 'getUploadFiles':
        return (API.getUploadFile(Vendor=session['Vendor'], Site = request.form.get('site', None) , TimeStart = request.form.get('time_start', '01/01/0001')  , TimeEnd = request.form.get('time_end', '12/31/9999')))

    # 合併兩個或多個檔案(使用者選取多個檔案做篩選時)
    if req == 'MergeFile':
        orderList = request.form.get('orderList', None).split(',')
        orderSite = request.form.get('orderSite', None)
        orderType = request.form.get('orderType', None)
        title = ''
        columnList = [u'收件人手機', u'收件人姓名', u'商品名稱', u'訂單日期', u'訂單金額']
        for idx,i in enumerate(orderList):
            fname = i
            if idx == 0:    # 先讀取第一個選取的檔案欄位做基底
                if orderType =='AIexcel':    # 將後續檔案 dataFrame 依序 append到後面
                    Module = {u'收件人手機':u'收件人手機'}
                    df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
                    FilterTitle = u'創建時間:--'
                elif orderType =='allFile':
                    Module = {u'收件人手機':u'收件人手機',u'收件人姓名':u'收件人姓名',u'商品名稱':u'商品名稱',u'訂單日期':u'付款日期',u'訂單金額':u'商品總價'}
                    df = pd.read_csv('AIexcel/' +fname , sep=',', encoding='utf8',low_memory=False)
                    FilterTitle = u'所有已上傳名單'
                else:
                    Module = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= fname))
                    df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
                if len(Module)<1:
                    return json.dumps({'BuyProductNameList':{'NotCreateModule':'NotCreateModule'}})
                haveColumnsList = []
                haveColumnsDict = {}
                for i in  columnList:
                    if Module[i] in df.columns:
                        haveColumnsList.append(Module[i])
                        haveColumnsDict[Module[i]] = i
                df = df[haveColumnsList]
                df.rename(columns= haveColumnsDict, inplace=True)
            else:       # 將後續檔案 dataFrame 依序 append到後面
                if orderType =='AIexcel':
                    new_df_Module = {u'收件人手機':u'收件人手機'}
                    new_df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
                elif orderType =='allFile':
                    new_df_Module = {u'收件人手機':u'收件人手機',u'收件人姓名':u'收件人姓名',u'商品名稱':u'商品名稱',u'訂單日期':u'付款日期',u'訂單金額':u'商品總價'}
                    new_df = pd.read_csv('AIexcel/' +fname , sep=',', encoding='utf8',low_memory=False)
                else:
                    new_df_Module = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= fname))
                    new_df = pd.read_csv(orderType + '/' +fname , sep=',', encoding='utf8',low_memory=False)
                if len(new_df_Module)<1:
                    return json.dumps({'BuyProductNameList':{'NotCreateModule':'NotCreateModule'}})
                haveColumnsList = []
                haveColumnsDict = {}
                for i in  columnList:
                    if new_df_Module[i] in df.columns:
                        haveColumnsList.append(new_df_Module[i])
                        haveColumnsDict[new_df_Module[i]] = i
                new_df = new_df[haveColumnsList]
                new_df.rename(columns=haveColumnsDict, inplace=True)

                res = pd.concat([df, new_df],axis=0, sort=False).drop_duplicates().reset_index(drop=True)

        # 依照檔案類型儲存到資料夾
        if orderType == 'uploadExl' or orderType == 'filteredExl' or orderType == 'messageExl':
            TimeStart = res[u'訂單日期'].apply(pd.to_datetime).min().strftime('%Y/%m/%d %H:%M:%S')
            TimeEnd = res[u'訂單日期'].apply(pd.to_datetime).max().strftime('%Y/%m/%d %H:%M:%S')
            if orderType == 'uploadExl':
                FilterTitle = orderSite + u':' + TimeStart +'~'+ TimeEnd
            elif orderType == 'filteredExl':
                FilterTitle = u'已篩選名單:' + TimeStart +'~'+ TimeEnd
            elif orderType == 'messageExl':
                FilterTitle = u'簡訊名單:' + TimeStart +'~'+ TimeEnd
        filename = str(uuid.uuid4().hex) + '.csv'
        if orderType =='allFile':
            res.to_csv('AIexcel/' + filename, sep=',', encoding='utf_8_sig',index=0)
        else:
            res.to_csv(orderType + '/' + filename, sep=',', encoding='utf_8_sig',index=0)

        # 儲存轉旋模組
        for idx,i in enumerate(columnList):
            API.storeModule(Vendor=session['Vendor'], defColumn=i, fname=filename,  VendorColumn=i)
        if u'商品名稱' in res.columns:
            BuyProductName = (res.drop_duplicates([u'商品名稱']))[u'商品名稱'].values.tolist()
        else:
            BuyProductName = []
        excelList = res.columns.tolist()
        return json.dumps({'excelList': excelList, 'BuyProductName': BuyProductName, 'FileName':filename ,'Title':FilterTitle})
    return None

# 發送測試簡訊
@app.route("/sendTestMessage/<fname>/<cells>", methods=['GET'])
def sendTestMessage(fname, cells):
    df = pd.read_csv('messageExl/' + fname , sep=',', encoding='utf8',low_memory=False)
    m = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= fname))
    cell = cells.split(",")
    message = df[u'簡訊內容'].tolist()
    sendMessage.sendFunction(cell = cell, message=message)
    return 'OK'

# 發送簡訊
@app.route("/sendMessage/<fname>/<aftertime>/<dlvtime>/<batch>/<start>/<end>", methods=['GET'])
def _sendMessage(fname,aftertime, dlvtime, batch, start, end):
    print(fname,aftertime, dlvtime, batch, start, end)
    df = pd.read_csv('messageExl/' + fname , sep=',', encoding='utf8',low_memory=False)
    m = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= fname))

    if end!='No' and start!='No':
        if int(end)< len(df.index):
            df = df[int(start):int(end)+1]
            newFname = str(uuid.uuid4().hex) + '.csv'
            df.to_csv('messageExl/' + newFname , sep=',', encoding='utf_8_sig',index=0)
            columnList = [u'收件人手機', u'收件人姓名', u'商品名稱', u'訂單日期', u'訂單金額']
            for idx,i in enumerate(columnList):
                try:
                    API.storeModule(Vendor=session['Vendor'], defColumn=i, fname= newFname,  VendorColumn= m[i])
                except:
                    pass
        else:
            return 'numberLarge'
    else:
        newFname = fname
        API.changeMessageFileSendStatus(fname)  # 將DB.MessageFile簡訊狀態改為已寄送
    cell = df[m[u'收件人手機']].tolist()
    message = df[u'簡訊內容'].tolist()
    msgidList = {}
    # 一次發送全部
    if dlvtime =='No' and batch =='No':
        msgidList = sendMessage.sendFunction_batch(cell = cell, message=message , dlvtime=aftertime)

    else:    # 分批發送
        for i in range(1, len(cell)/int(batch) +2):
            the_dlvtime = (i-1)* int(dlvtime) + (int(aftertime))
            if i == len(cell)/int(batch) +2:
                res = sendMessage.sendFunction_batch(cell = cell[((i-1)* int(batch)):len(cell)], message=message[((i-1)* int(batch)):len(cell)], dlvtime=the_dlvtime)
            else:
                res = sendMessage.sendFunction_batch(cell = cell[((i-1)* int(batch)):(i* int(batch))], message=message[((i-1)* int(batch)):(i* int(batch))], dlvtime=the_dlvtime)
            for j in res:
                msgidList[j]= res[j]
    msgidList = {str(k):str(v) for k,v in msgidList.items()}
    print msgidList
    try:
        import sys
        sys.stdout.flush()
    except:
        pass
    Number = len(df.index) # 資料筆數
    API.storeSendMessageResult(FileName = newFname,MessageFileName = fname, Vendor=session['Vendor'], number = Number) # 創建簡訊結果資料到DB

    # 將三竹簡訊回傳之messageID寫到excel後msgid欄位以做後續簡訊狀態追蹤
    df["msgid"] = df[m[u'收件人手機']].apply(lambda x:str(msgidList[str(x)]) if str(x) in msgidList  else '-')
    df.to_csv('messageExl/' + newFname , sep=',', encoding='utf_8_sig',index=0)

    if os.path.isfile('AIexcel/' + session['Vendor'] + '_ga.csv'):
        df_ga = pd.read_csv('AIexcel/'+ session['Vendor'] + '_ga.csv' , sep=',', encoding='utf_8_sig',low_memory=False)
        phones = df["msgid"].tolist()
        new_df = DataFrame ({}, columns = [u'收件人手機','UserLabel', 'next_time'])
        new_df[u'收件人手機'] = phones
        new_df['UserLabel'] = new_df['UserLabel'].fillna(u'尚未點擊')
        today = dt.date.today()
        new_df['next_time'] = today+pd.DateOffset(days=10)
        res = pd.concat([df_ga, new_df],axis=0, sort=False).drop_duplicates(subset=u'收件人手機', keep='last').reset_index(drop=True)
        res[u'收件人手機'] = res[u'收件人手機'].astype(dtype=np.int64,errors='ignore')
        res.to_csv('AIexcel/'+ session['Vendor'] + '_ga.csv' , sep=',', encoding='utf_8_sig',index=0)
    else:
        phones = df["msgid"].tolist()
        new_df = DataFrame ({}, columns = [u'收件人手機','UserLabel', 'next_time'])
        new_df[u'收件人手機'] = phones
        new_df['UserLabel'] = new_df['UserLabel'].fillna(u'尚未點擊')
        today = dt.date.today()
        new_df['next_time'] = today+pd.DateOffset(days=10)
        new_df[u'收件人手機'] = new_df[u'收件人手機'].astype(dtype=np.int64, errors='ignore')
        new_df.to_csv('AIexcel/'+ session['Vendor'] + '_ga.csv' , sep=',', encoding='utf_8_sig',index=0)
    return 'OK'

# 上傳Excel檔案
@app.route('/uploadExcel',methods=['GET','POST'])
def uploadExcel():
    if not session.get('logged_in'):
        return redirect(url_for('logingpage'))
    if request.method == 'GET':
        username = session['Vendor']
        return render_template("uploadExcel.html", username=username)
    if request.method == 'POST':
        try:
            username = session['Vendor']
            filedata = request.files['upload']
            FileFrom = request.form.get('location')
            if FileFrom =='other':
                FileFrom = request.form.get('other_location','其他')
            FileTimeStart = request.form.get('from')
            FileTimeEnd = request.form.get('to')
            fname = str(uuid.uuid4().hex) + '.csv'
            tmpFname = 'uploadTmp/' + session['Vendor'] + '.csv'
            mimetype = filedata.content_type
            start = time.time()

            # 判斷檔案類型為xlsx或是csv
            if filedata and mimetype== 'application/octet-stream'or mimetype=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                df =pd.read_excel(filedata, encoding=sys.getfilesystemencoding())
                counter = len(df.index)
                df.to_csv('uploadExl/' + fname, sep=',', encoding='utf_8_sig',index=0)
                end = time.time()
                print ("Write xlsx Data taken time: ", end - start, "seconds.")
                API.storeUploadFile(fname, FileFrom, FileTimeStart, FileTimeEnd, session['Vendor'], counter)
                return redirect(url_for('newmodule'))
            if filedata and mimetype=='text/csv':
                filedata.save(tmpFname)
                ec = chardet.detect(open(tmpFname).readline())['encoding']
                with codecs.open(tmpFname, "r", ec, errors="ignore") as sourceFile:
                    with codecs.open('uploadExl/' + fname, "wb", "utf-8") as targetFile:
                        targetFile.write(sourceFile.read())
                df = pd.read_csv('uploadExl/' + fname , encoding='utf8',low_memory=False)
                df.to_csv('uploadExl/' + fname, sep=',', encoding='utf_8_sig',index=0)
                counter = len(df.index)
                end = time.time()
                print ("Write csv Data taken time: ", end - start, "seconds.")
                API.storeUploadFile(fname, FileFrom, FileTimeStart, FileTimeEnd, session['Vendor'], counter)
                return redirect(url_for('newmodule'))
            else:
                print ("not True type file")
                return render_template("uploadExcel.html",error=u'上傳失敗，請檢查並重新上傳一次檔案。',username=username)
        except Exception,e:
            print str(e)
            return render_template("uploadExcel.html",error=u'上傳失敗，請檢查並重新上傳一次檔案。', username=username)

# 登入頁面
@app.route('/loginpage')
def logingpage():
    return render_template("logingpage.html")
# 登入
@app.route('/login',methods=['POST'])
def login():
    if request.method == 'POST':
        account=request.form.get("account")
        password=request.form.get("password")
        loginStatus = json.loads(API.login(account = account, password = password))

        if loginStatus['status']=="Success":
            session['logged_in'] = True
            session['Vendor'] = loginStatus['Vendor']
            return redirect(url_for('uploadExcel'))
    return redirect(url_for('uploadExcel'))

# 登出
@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['Vendor'] = ''
    return redirect(url_for('index'))


# 註冊
@app.route('/signup',methods=['POST'])
def signup():
    if request.method == 'POST':
        account=request.form.get("account")
        password=request.form.get("password")
        loginStatus = json.loads(API.singup(account = account, password = password))
        if loginStatus['status']=="Success":
            session['logged_in'] = True
            session['Vendor'] = loginStatus['Vendor']

            return redirect(url_for('uploadExcel'))
    return redirect(url_for('uploadExcel'))

# 以篩選名單總覽頁面
@app.route('/allModule')
def allModule():
    if not session.get('logged_in'):
        return redirect(url_for("logingpage"))

    elif len(API.getFilterFile(session['Vendor']))<1:
        return redirect(url_for('index'))
    username = session['Vendor']
    FilterFiles = json.loads(API.getFilterFile(session['Vendor']))
    return render_template("allModule.html",FilterFiles = FilterFiles, username=username)

# 建立轉換模組頁面
@app.route('/newmodule')
def newmodule():
    if not session.get('logged_in'):
        return redirect(url_for("logingpage"))
    files = json.loads(API.getUploadFile(Vendor=session['Vendor']))
    if len(files) < 1:
        return redirect(url_for("uploadExcel"))
    fname = files[0]['FileName']
    username = session['Vendor']
    return render_template("newmodule.html", files=files,username=username)
# 儲存轉換模組
@app.route('/storeModule', methods=['POST'])
def storeModule():
    defColumn = request.form.getlist('defColumn')
    VendorColumn = request.form.getlist('VendorColumn')
    fname = request.form.get('fname')
    files = json.loads(API.getUploadFile(Vendor=session['Vendor']))
    username = session['Vendor']
    df = pd.read_csv('uploadExl/' + fname, sep=',', encoding='utf8',low_memory=False)
    try:
        errorsList = df.loc[~df[VendorColumn[1]].astype('unicode').str.isdigit(), VendorColumn[1]].tolist()
    except:
        return render_template("newmodule.html", files=files,username=username,status='columns_error')
    if errorsList:
        try:
            return render_template("newmodule.html", files=files,username=username,status='error', errors=errorsList)
        except:
            return render_template("newmodule.html", files=files,username=username,status='columns_error')

    for idx,i in enumerate(defColumn):
        API.storeModule(Vendor=session['Vendor'], defColumn=i, fname=fname,  VendorColumn=VendorColumn[idx])

    ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName=fname))

    df = df[[ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期'],ModuleMapping[u'商品名稱'], ModuleMapping[u'訂單金額']]]
    df.columns=[u'收件人姓名', u'收件人手機', u'付款日期', u'商品名稱',u'商品總價']

    if not os.path.isfile('AIexcel/'+ session['Vendor'] + '.csv'):
        df[u'收件人手機'] = df[u'收件人手機'].astype(dtype=np.int64, errors='ignore')
        df.to_csv('AIexcel/' + session['Vendor'] + '.csv', sep=',', encoding='utf_8_sig',index=0)
    else:
        old_df = pd.read_csv('AIexcel/' + session['Vendor'] + '.csv', sep=',', encoding='utf8',low_memory=False)
        res = pd.concat([old_df, df],axis=0, sort=False).drop_duplicates().reset_index(drop=True)
        res[u'收件人手機'] = res[u'收件人手機'].astype(dtype=np.int64, errors='ignore')
        res.to_csv('AIexcel/' + session['Vendor'] + '.csv', sep=',', encoding='utf_8_sig',index=0)
    return render_template("newmodule.html", files=files,username=username,status='success', errors=u'已成功建立轉換模組')
# 篩選頁面
@app.route('/')
@app.route('/index')
def index(err=None):
    if not session.get('logged_in'):
        return render_template("logingpage.html")
    username = session['Vendor']
    return render_template("index.html", err=err,username=username)

# 篩選名單
@app.route('/filter' , methods=['GET', 'POST'])
def filter():
    if request.method == 'POST':
        f = request.form.get("fname")   # 檔名
        Type = request.form.get("select_site") # 檔案類型
        filterChekbox = request.form.getlist('filterChekbox') # 要篩選的條件List
        otherfilterChekbox =  request.form.getlist('otherfilterChekbox') # 其他篩選條件List
        otherNfilterChekbox = request.form.getlist('otherNfilterChekbox') # 其他排除條件List
        ReservedCol = request.form.getlist('OutputColumn') # 篩選完要保留的欄位
        sortKey = request.form.get('sort_key') # 排序欄位
        print("-----Filter-----")
        print("Fname:",f)
        print("Type:",Type)
        print("filterChekbox:",filterChekbox)
        print("otherfilterChekbox:",otherfilterChekbox)
        print("otherNfilterChekbox:",otherNfilterChekbox)
        print("sortKey:", sortKey)
        print("-----FilterEnd-----")
        # 判斷檔案類型讀取檔案
        if Type == 'filteredExl':
            the_type = 'filteredExl/'
            fname = the_type +'/' + f
            ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName=f))
        elif Type == 'AIexcel':
            ModuleMapping = {u'收件人手機':u'收件人手機'}
            the_type = 'AIexcel/'
            fname = the_type + f
        elif Type == 'messageExl':
            ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName=f))
            the_type = 'messageExl/'
            fname = the_type + f
        elif Type == 'allFile':
            ModuleMapping = {u'收件人手機':u'收件人手機',u'收件人姓名':u'收件人姓名',u'商品名稱':u'商品名稱',u'訂單日期':u'付款日期',u'訂單金額':u'商品總價'}
            the_type = 'AIexcel/'
            fname = 'AIexcel/' + f
        else:
            the_type = 'uploadExl/'
            fname = the_type +'/' + f
            ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName=f))

        df = pd.read_csv(fname , sep=',', encoding='utf8',low_memory=False)
        if df[ModuleMapping[u'收件人手機']].dtypes =='float64':
            df[ModuleMapping[u'收件人手機']] = df[ModuleMapping[u'收件人手機']].fillna(0).astype(int)
            df = df[df[ModuleMapping[u'收件人手機']] != 0]
        df.to_csv(fname, sep=',', encoding='utf-8-sig',index=0)
        data_list = df.columns.tolist()
        FilterContent = ''
        for item in data_list:
            i = "DistanceDay" # 距離上次購買時間
            if key_for_value(ModuleMapping, item)==u'訂單日期' and i in filterChekbox:
                c = request.form.get(i)
                Operator = request.form.get(i+"_Operator")
                df[ModuleMapping[u'訂單日期']] = pd.to_datetime(df[ModuleMapping[u'訂單日期']],errors='coerce')
                df = df[pd.notnull(df[ModuleMapping[u'訂單日期']])]
                if c == "Other":    # 日期為使用者自定義期限
                    c  = request.form.get("Other"+i)
                if Operator =='bigger': # 大於
                    removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[ModuleMapping[u'訂單日期']].astype(dtype='datetime64',errors='ignore') > datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'上次訂單日期距今' + u'大於' + str(c) + u'天。')
                elif Operator =='biggerAnd':    # 大於等於
                    removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[ModuleMapping[u'訂單日期']].astype(dtype='datetime64',errors='ignore') >= datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'上次訂單日期距今' + u'大於等於' + str(c) + u'天。')
                elif Operator =='equal':    # 等於
                    removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[ModuleMapping[u'訂單日期']].astype(dtype='datetime64',errors='ignore') == datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'上次訂單日期距今' + u'等於' + str(c) + u'天。')
                elif Operator =='smaller':  # 小於
                    removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[ModuleMapping[u'訂單日期']].astype(dtype='datetime64',errors='ignore') < datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'上次訂單日期距今' + u'小於' + str(c) + u'天。')
                elif Operator =='smallerAnd':   # 小於等於
                    removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[ModuleMapping[u'訂單日期']].astype(dtype='datetime64',errors='ignore') <= datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'上次訂單日期距今' + u'小於等於' + str(c) + u'天。')
                df = df[df[ModuleMapping[u'收件人手機']].isin(removeCell) == False]
            i = "BuyTimes"  # 購買次數
            if key_for_value(ModuleMapping, item)==u'收件人手機' and i in filterChekbox:
                c = request.form.get(i)
                df = df[pd.notnull(df[ModuleMapping[u'收件人手機']])]
                if df[ModuleMapping[u'收件人手機']].dtypes =='int':
                    df = df[df[ModuleMapping[u'收件人手機']] != 0]
                if c == "Other":
                    c  = request.form.get("Other"+i)
                groupData = df.groupby(ModuleMapping[u'收件人手機'])
                Operator = request.form.get(i+"_Operator")
                if Operator =='bigger':
                    reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).size().reset_index(name='countsBuyThings').groupby(ModuleMapping[u'收件人手機']).filter(lambda x: x[ModuleMapping[u'收件人手機']].count() > int(c))[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'購買次數' + u'大於' + str(c) + u'。')
                elif Operator =='biggerAnd':
                    reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).size().reset_index(name='countsBuyThings').groupby(ModuleMapping[u'收件人手機']).filter(lambda x: x[ModuleMapping[u'收件人手機']].count() >= int(c))[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'購買次數' + u'大於等於' + str(c) + u'。')
                elif Operator =='equal':
                    reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).size().reset_index(name='countsBuyThings').groupby(ModuleMapping[u'收件人手機']).filter(lambda x: x[ModuleMapping[u'收件人手機']].count() == int(c))[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'購買次數' + u'等於' + str(c) + u'。')
                elif Operator =='smaller':
                    reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).size().reset_index(name='countsBuyThings').groupby(ModuleMapping[u'收件人手機']).filter(lambda x: x[ModuleMapping[u'收件人手機']].count() < int(c))[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'購買次數' + u'小於' + str(c) + u'。')
                elif Operator =='smallerAnd':
                    reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).size().reset_index(name='countsBuyThings').groupby(ModuleMapping[u'收件人手機']).filter(lambda x: x[ModuleMapping[u'收件人手機']].count() <= int(c))[ModuleMapping[u'收件人手機']].values.tolist()
                    FilterContent = FilterContent + (u'購買次數' + u'小於等於' + str(c) + u'。')
                df = df[df[ModuleMapping[u'收件人手機']].isin(reserveCell)]

            i = "OnceBuyCost" # 單次購買金額
            if key_for_value(ModuleMapping, item)==u'訂單金額' and i in filterChekbox:
                c = request.form.get(i)
                if c == "Other":
                    c  = request.form.get("Other"+i)
                c = c.split("-")
                try:
                    k = c[1]
                except:
                    c = ['0',c[0]]
                if int(c[0])> int(c[1]):
                    k = c[0]
                    c[0] = c[1]
                    c[1] = k
                reserveCell = df.groupby([ModuleMapping[u'收件人手機'], ModuleMapping[u'訂單日期']]).filter(lambda x: x[ModuleMapping[u'訂單金額']].sum()>int(c[0]) and x[ModuleMapping[u'訂單金額']].sum()<int(c[1]))[ModuleMapping[u'收件人手機']].values.tolist()
                df = df[df[ModuleMapping[u'收件人手機']].isin(reserveCell)]
                FilterContent = FilterContent + (u'單次購買金額' +  u'介於' + str(c[0]) + "~" + str(c[1]) + u'。')
            i = "TotalBuyCost" # 總計購買金額
            if key_for_value(ModuleMapping, item)==u'訂單金額' and i in filterChekbox:
                c = request.form.get(i)
                if c == "Other":
                    c  = request.form.get("Other"+i)
                c = c.split("-")
                try:
                    k = c[1]
                except:
                    c = ['0',c[0]]
                groupData = df.groupby(ModuleMapping[u'收件人手機'])
                df[item] = pd.to_numeric(df[item], errors='coerce')
                df = groupData.filter(lambda x: x[item].sum()<int(c[1]) and x[item].sum()>int(c[0]))
                FilterContent = FilterContent + (u'總訂單金額' + u'介於' + str(c[0]) + "~" +str(c[1])+ u'。')
            i = "BuyProductName" # 購買商品名稱為xxx
            if key_for_value(ModuleMapping, item)==u'商品名稱' and i in filterChekbox:
                productList = request.form.getlist('BuyProductName')
                AndOrList = request.form.getlist('AndOrList')
                OperatorList = request.form.getlist('BuyProductName_Operator')
                QtList = request.form.getlist('OtherBuyProductName')
                reserveCell = []
                import sys
                reload(sys)
                sys.setdefaultencoding('utf-8')
                outreserveCell = df.drop_duplicates(ModuleMapping[u'收件人手機'])[ModuleMapping[u'收件人手機']].values.tolist()
                groupDF = df.groupby([ModuleMapping[u'收件人手機'],ModuleMapping[u'商品名稱']]).size().reset_index(name='countsBuyProduct')
                if len(groupDF)>0:
                    for idx, elem in enumerate(productList):
                        if (QtList[idx])=='':
                            QtList[idx] = 0
                        if OperatorList[idx]=='bigger':
                            reserveCell = groupDF[(groupDF[ModuleMapping[u'商品名稱']]==elem) & (groupDF['countsBuyProduct'] > int(QtList[idx]))][ModuleMapping[u'收件人手機']].values.tolist()
                            FilterContent = FilterContent + (u'購買' + str(elem)  +  u'次數大於' + str(QtList[idx])  + u'。')
                        elif OperatorList[idx] =='biggerAnd':
                            reserveCell = groupDF[(groupDF[ModuleMapping[u'商品名稱']]==elem) & (groupDF['countsBuyProduct'] >= int(QtList[idx]))][ModuleMapping[u'收件人手機']].values.tolist()
                            FilterContent = FilterContent + (u'購買' + str(elem)  +  u'次數大於等於' + str(QtList[idx])  + u'。')
                        elif OperatorList[idx] =='equal':
                            reserveCell = groupDF[(groupDF[ModuleMapping[u'商品名稱']]==elem) & (groupDF['countsBuyProduct'] == int(QtList[idx]))][ModuleMapping[u'收件人手機']].values.tolist()
                            FilterContent = FilterContent + (u'購買' + str(elem)  +  u'等於' + str(QtList[idx])  + u'。')
                        elif OperatorList[idx] =='smaller':
                            reserveCell = groupDF[(groupDF[ModuleMapping[u'商品名稱']]==elem) & (groupDF['countsBuyProduct'] < int(QtList[idx]))][ModuleMapping[u'收件人手機']].values.tolist()
                            FilterContent = FilterContent + (u'購買' + str(elem)  +  u'次數小於' + str(QtList[idx])  + u'。')
                        elif OperatorList[idx] =='smallerAnd':
                            reserveCell = groupDF[(groupDF[ModuleMapping[u'商品名稱']]==elem) & (groupDF['countsBuyProduct'] <= int(QtList[idx]))][ModuleMapping[u'收件人手機']].values.tolist()
                            FilterContent = FilterContent + (u'購買' + str(elem)  +  u'次數小於等於' + str(QtList[idx])  + u'。')
                        if idx==0:
                            outreserveCell = reserveCell
                        elif AndOrList[idx-1]=='and':
                            outreserveCell = list(set(reserveCell) & set(outreserveCell))
                        elif AndOrList[idx-1]=='or':
                            outreserveCell = list(set().union(reserveCell, outreserveCell))
                        else:
                            print "???"
                    df = df[df[ModuleMapping[u'收件人手機']].isin(outreserveCell)]
            # 其他篩選條件
            for j in otherfilterChekbox:
                if request.form.get(j)== item:
                    filterValue= request.form.get(j+"_Value")
                    Operator = request.form.get(j+"_Operator")
                    if filterValue.isdigit() and Operator!='similar':
                        filterValue = int(filterValue)
                    elif (('datetime64' in str(df[item].dtypes)) or  key_for_value(ModuleMapping, item)==u'簡訊日期' or key_for_value(ModuleMapping, item)==u'訂單日期') and is_date(filterValue) and Operator!='similar':
                        df[item] = df[item].astype(dtype='datetime64',errors='ignore')
                        filterValue = parse(filterValue)
                    if Operator =='bigger':
                        FilterContent = FilterContent + (item + u'大於' + str(filterValue) + u'。')
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] > filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    elif Operator =='biggerAnd':
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] >= filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (item + u'大於等於' + str(filterValue) + u'。')
                    elif Operator =='equal':
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] == filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (item + u'等於' + str(filterValue) + u'。')
                    elif Operator =='smaller':
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] < filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (item + u'小於' + str(filterValue) + u'。')
                    elif Operator =='smallerAnd':
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] <= filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (item + u'小於等於' + str(filterValue) + u'。')
                    elif Operator =='similar':
                        saveCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item].astype('object').str.contains(filterValue)).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (item + u'相似於' + filterValue + u'。')
                    df = df[df[ModuleMapping[u'收件人手機']].isin(saveCell) == True]
            # 其他排除條件
            for j in otherNfilterChekbox:
                if request.form.get(j)== item:
                    filterValue= request.form.get(j+"_Value")
                    Operator = request.form.get(j+"_Operator")
                    if filterValue.isdigit() and Operator!='similar':
                        filterValue = int(filterValue)
                    elif (('datetime64' in str(df[item].dtypes)) or  key_for_value(ModuleMapping, item)==u'簡訊日期' or key_for_value(ModuleMapping, item)==u'訂單日期') and is_date(filterValue) and Operator!='similar':
                        df[item] = df[item].astype(dtype='datetime64',errors='ignore')
                        filterValue = parse(filterValue)
                    if Operator =='bigger':
                        FilterContent = FilterContent + (u'排除' +item + u'大於' + str(filterValue) + u'。')
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] > filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                    elif Operator =='biggerAnd':
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] >= filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (u'排除' + item + u'大於等於' + str(filterValue) + u'。')
                    elif Operator =='equal':
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] == filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (u'排除' + item + u'等於' + str(filterValue) + u'。')
                    elif Operator =='smaller':
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] < filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (u'排除' + item + u'小於' + str(filterValue) + u'。')
                    elif Operator =='smallerAnd':
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item] <= filterValue).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (u'排除' + item + u'小於等於' + str(filterValue) + u'。')
                    elif Operator =='similar':
                        removeCell = df.groupby([ModuleMapping[u'收件人手機']]).filter(lambda x: (x[item].astype('object').str.contains(filterValue)).any())[ModuleMapping[u'收件人手機']].values.tolist()
                        FilterContent = FilterContent + (u'排除' + item + u'相似於' + filterValue + u'。')
                    df = df[df[ModuleMapping[u'收件人手機']].isin(removeCell) == False]

        fname = str(uuid.uuid4().hex) + '.csv'
        FilterTitle = request.form.get("FilterTitle")

        if FilterTitle == u'所有已上傳名單' or u'創建時間' in FilterTitle:
            FileFrom = u'所有已上傳名單'
            FileTime_start = json.loads(API.getFromEndTime(session['Vendor']))['start']
            FileTime_end = json.loads(API.getFromEndTime(session['Vendor']))['end']
        else:
            FileFrom = FilterTitle.split(":")[0]
            FileTime_start = FilterTitle.split(":")[1].split("~")[0]
            FileTime_end = FilterTitle.split("~")[1].split("(")[0]
        counter = len(df.drop_duplicates(ModuleMapping[u'收件人手機']))
        API.storeFilterFile(FromUploadFileName= f,FileFrom=FileFrom, FileTime_start = FileTime_start, FileTime_end =FileTime_end, FilterContent=FilterContent,fname = fname, Vendor=session['Vendor'], number = counter)
        columnList = [u'收件人手機', u'收件人姓名', u'商品名稱', u'訂單日期', u'訂單金額']

        for idx,i in enumerate(columnList):
            try:
                API.storeModule(Vendor=session['Vendor'], defColumn=i, fname= fname,  VendorColumn= ModuleMapping[i])
            except:
                pass
        if sortKey != "" and sortKey!=None:
            df = df.sort_values(by = [sortKey, ModuleMapping[u'收件人手機']])
        else:
            if u'訂單日期' in ModuleMapping:
                df = df.sort_values(by = [ModuleMapping[u'訂單日期'], ModuleMapping[u'收件人手機']])

        data_df = pd.DataFrame(df, columns=ReservedCol)
        data_df.columns = ReservedCol
        data_df.to_csv('filteredExl/' + fname, sep=',', encoding='utf_8_sig',index=0)

        return redirect(url_for('output',filename = fname, type="filteredExl"))
    return redirect(url_for('index'))
@app.route('/messageModule',methods=['GET','POST'])
def messageModule():
    # 呼叫簡訊模組網頁
    if request.method == 'GET':
        if not session.get('logged_in'):
            return redirect(url_for("logingpage"))
        FilterFiles = json.loads(API.getFilterFile(session['Vendor']))
        AIFiles = json.loads(API.getAIfilterFile(session['Vendor']))
        if len(FilterFiles)<1:
            return redirect(url_for('index'))
        username = session['Vendor']
        return render_template("messageModule.html", FilterFiles={'FilterFiles': FilterFiles, 'AIFiles': AIFiles}, username=username)
    # 儲存簡訊模組
    if request.method == 'POST':
        originalFileName = request.form.get("useModule")
        FileType = 'filteredExl'
        onlyCell = request.form.get("OnlyCell", None)
        MessageContent = request.form.get("MessageContent")
        if not os.path.isfile('filteredExl/' + originalFileName):
            FileType = 'AIexcel'
            df = pd.read_csv('AIexcel/' + originalFileName , sep=',', encoding='utf8',low_memory=False)
            ModuleMapping = {u'收件人手機':u'收件人手機',u'收件人姓名':u'收件人姓名'}
            data = API.getOneAIfilterFile(originalFileName)
        else:
            df = pd.read_csv('filteredExl/' + originalFileName , sep=',', encoding='utf8',low_memory=False)
            data = API.getOneFilterFile(originalFileName)
            ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName= originalFileName))

        if onlyCell=='True' and FileType=='filteredExl':
            df = pd.DataFrame(df, columns=[ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機']])
            df.columns = [ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機']]
        df = df[pd.notnull(df[ModuleMapping[u'收件人手機']])]
        df = df.drop_duplicates(ModuleMapping[u'收件人手機'])

        # 處理utm網址
        user_urls = {}
        url = request.form.get("WebUrl", 'http://3.208.233.139/')
        UUID = str(uuid.uuid4().hex)
        fname = UUID + '.csv'
        utm_source = "AICRM-" + UUID
        if '?' in url:
            url = url + '&utm_source=' + utm_source
        else:
            url = url + '?utm_source=' + utm_source

        CampaignMedium = request.form.get("CampaignMedium",None)
        CampaignContent= request.form.get("CampaignContent",None)
        CampaignName = request.form.get("CampaignName",None)
        CampaignTerm = request.form.get("CampaignTerm",None)
        if CampaignName:
            CampaignName = CampaignName.replace(" ", "")
            url = url + "&utm_campaign=" + urllib.quote(CampaignName.encode('utf-8'))
        if CampaignTerm:
            CampaignTerm = CampaignTerm.replace(" ", "")
            url = url + "&utm_term=" + urllib.quote(CampaignTerm.encode('utf-8'))
        if CampaignContent:
            CampaignContent = CampaignContent.replace(" ", "")
            url = url + "&utm_content=" + urllib.quote(CampaignContent.encode('utf-8'))
        if CampaignMedium:
            CampaignMedium = CampaignMedium.replace(" ", "")
            url = url + '&utm_medium=' + urllib.quote(CampaignMedium.encode('utf-8')) + "-" + strftime("%y%m%d", gmtime()) + "-"
        else:
            url = url + '&utm_medium=' + strftime("%y%m%d", gmtime()) + "-"



        if FileType=='filteredExl':
            API.storeMessageFile(fname, session['Vendor'], data['FileFrom'], data['FileTime_start'], data['FileTime_end'] , CampaignMedium, CampaignName, data['Number'], data['FromUploadFileName'], (MessageContent)+url, originalFileName)
            columnList = [u'收件人手機', u'收件人姓名', u'商品名稱', u'訂單日期', u'訂單金額']
            try:
                for idx,i in enumerate(columnList):
                    API.storeModule(Vendor=session['Vendor'], defColumn=i, fname=fname,  VendorColumn= ModuleMapping[i])
            except:
                pass
        else:
            API.storeMessageFile(fname, session['Vendor'], u'AI篩選名單', data['CreateTime'], data['CreateTime'] , CampaignMedium, CampaignName, data['Number'], data['FileName'],(MessageContent) +url, originalFileName)
            columnList = [u'收件人手機', u'收件人姓名']
            for idx,i in enumerate(columnList):
                API.storeModule(Vendor=session['Vendor'], defColumn=i, fname=fname,  VendorColumn= ModuleMapping[i])
        # 建立線程
        async_function(url, MessageContent, df[ModuleMapping[u'收件人手機']].values.tolist(), df, fname)
        return redirect(url_for("allMessageFile"))

# 所有簡訊名單列表
@app.route('/allMessageFile')
def allMessageFile():
    if not session.get('logged_in'):
        return redirect(url_for("logingpage"))

    MessageFiles = json.loads(API.getMessageFile(session['Vendor']))
    if len(MessageFiles)<1:
            return redirect(url_for('messageModule'))
    MessageResult = json.loads(API.getSendMessageResult(session['Vendor']))
    username = session['Vendor']
    return render_template("allMessageFile.html",MessageFiles = MessageFiles, MessageResult= MessageResult,username=username)


# 取得excel檔案column名稱
@app.route('/get_df_column/<type>/<fname>')
def get_df_column(fname, type):
    if type == 'uploadExl':
        df = pd.read_csv('uploadExl/' + fname , sep=',', encoding='utf8',low_memory=False)
        excelList = df.columns.tolist()
    elif type == 'filteredExl':
        df = pd.read_csv('filteredExl/' + fname , sep=',', encoding='utf8',low_memory=False)
        excelList = df.columns.tolist()
    elif type == 'messageExl':
        df = pd.read_csv('messageExl/' + fname , sep=',', encoding='utf8',low_memory=False)
        excelList = df.columns.tolist()
    elif type == 'AIexcel' or type == 'allFile':
        df = pd.read_csv('AIexcel/' + fname , sep=',', encoding='utf8',low_memory=False)
        excelList = df.columns.tolist()
    return json.dumps(excelList)

# 輸出excel檔案到html頁面
@app.route('/output/<type>/<filename>')
def output(type, filename):
    if type=="uploadExl":
        fname = 'uploadExl/' + filename
    if type=="filteredExl":
        fname = 'filteredExl/' + filename
    elif type=="messageExl":
        fname = 'messageExl/' + filename
    elif type=="AIexcel":
        fname = 'AIexcel/' + filename
        if not os.path.exists(fname):
            return redirect(url_for('index',err = '0'))
    x = pd.read_csv(fname , sep=',', encoding='utf8',low_memory=False)
    if len(x)>100:
        data = []
        for i in range(len(x.columns.tolist())):
            data.append(u'...')
        df2 = pd.DataFrame([data], columns = x.columns.tolist())
        x = x.head(50).append([df2,df2,df2, x.tail(50)], ignore_index=True)
    return render_template("output.html", fname=filename, type=type, data=x.to_html())

# 下載檔案(存手機號碼)
@app.route('/downloadOnlyCell/<type>/<filename>')
def downloadOnlyCell(type, filename):
    fname = filename
    print fname
    if not session.get('logged_in'):
        redirect(url_for("logingpage"))
    if type=="AIexcel":
        newfname = "AIexcel/onlyCell_" +filename
        filename = 'AIexcel/' + filename
        df = pd.read_csv(filename , sep=',', encoding='utf8',low_memory=False)
        data_df = pd.DataFrame(df, columns=['uuid'])
        data_df.columns = [u'手機號碼']
        data_df.to_csv(newfname, sep=',', encoding='utf_8_sig',index=0)
        return send_from_directory("./", newfname, as_attachment=True)
    else:
        newfname = type + "/onlyCell_" +filename
        filename = type + '/' + filename
        ModuleMapping = json.loads(API.getMappingData(Vendor=session['Vendor'], FileName=fname))

    if u'收件人姓名' in ModuleMapping and u'收件人手機' in ModuleMapping:
        df = pd.read_csv(filename , sep=',', encoding='utf8',low_memory=False)
        try:
            if type=="filteredExl" or type=="uploadExl":
                data_df = pd.DataFrame(df, columns=[ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機']])
                data_df.columns = [ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機']]
                data_df = data_df.drop_duplicates(ModuleMapping[u'收件人手機'])
            elif type=="messageExl":
                data_df = pd.DataFrame(df, columns=[ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機'], u'專屬網址', u'簡訊內容'])
                data_df.columns = [ModuleMapping[u'收件人姓名'], ModuleMapping[u'收件人手機'], u'專屬網址', u'簡訊內容']
                data_df = data_df.drop_duplicates(ModuleMapping[u'收件人手機'])
            elif type=="AIexcel":
                data_df = pd.DataFrame(df, columns=['uuid'])
                data_df.columns = [u'手機號碼']
            data_df.to_csv(newfname, sep=',', encoding='utf_8_sig',index=0)

            return send_from_directory("./", newfname, as_attachment=True)
        except:
            return redirect(url_for('newmodule'))
    else:
        return redirect(url_for('newmodule'))

# 下載檔案
@app.route('/download/<type>/<filename>')
def download(type, filename):
    if not session.get('logged_in'):
        redirect(url_for("logingpage"))
    if type=="uploadExl":
        filename = 'uploadExl/' + filename
    elif type=="filteredExl":
        filename = 'filteredExl/' + filename
    elif type=="messageExl":
        filename = 'messageExl/' + filename
    elif type=="AIexcel":
        filename = 'AIexcel/' + filename
    return send_from_directory("./", filename, as_attachment=True)

# 輸出AI篩選 excel檔案
@app.route('/AIoutput', methods=['GET', 'POST'])
def AIoutput():
    ai_quantity = request.form.get("ai_quantity")
    ai_days = request.form.get("ai_days")
    ai_price = request.form.get("ai_price")

    if ai_quantity=='':
        ai_quantity=100
    if ai_days=='':
        ai_days=30
    # if ai_price=='':
    #     ai_price='0-1000'
    # c = ai_price.split("-")
    # try:
    #     k = c[1]
    # except:
    #     c = ['0',c[0]]
    err = ''
    username = session['Vendor']
    try:
        df = AI.predicted_purchase_time(account=session['Vendor'],timesteap = int(ai_days))
        # df = df[df[u'平均交易金額'].between(int(c[0]),int(c[1]))]
        df = df.head(int(ai_quantity))
        df.reset_index(inplace=True)

        filename =  str(uuid.uuid4().hex) + '.csv'
        df.to_csv("AIexcel/" +filename, sep=',', encoding='utf_8_sig', index=False)
        counter = len(df.index)
        API.storeAIfilterFile(FileName = filename, Vendor=session['Vendor'], number=counter)

        if len(df)>1000:
            data = []
            for i in range(len(df.columns.tolist())):
                data.append(u'...')
            df2 = pd.DataFrame([data], columns = df.columns.tolist())
            df = df.head(500).append([df2,df2,df2, df.tail(500)], ignore_index=True)
        return render_template("output.html", fname=filename, type="AIexcel", data=df.to_html())
    except:
        err = 'err'
    return render_template("AIfilter.html",username=username, err='err')



# AI篩選頁面
@app.route('/AIfilter', methods=['GET', 'POST'])
def AIfilter():
    username = session['Vendor']
    return render_template("AIfilter.html",username=username)

# 所有AI篩選檔案列表
@app.route('/allAIfilter')
def allAIfilter():
    if not session.get('logged_in'):
        return redirect(url_for("logingpage"))
    AIfilterFiles = json.loads(API.getAIfilterFile(session['Vendor']))
    if len(AIfilterFiles)<1:
            return redirect(url_for('AIfilter'))
    username = session['Vendor']
    return render_template("allAIfilterFile.html",AIfilterFiles = AIfilterFiles,username=username)
@app.route("/GAtable", methods=["GET","POST"])
def GAtable():
    if request.method == 'POST':
        from bs4 import BeautifulSoup
        import json
        StoreData = []
        jsdata = request.form['javascript_data']
        jsdata = json.loads(jsdata)['html']
        soup = BeautifulSoup(jsdata, "lxml")

        output_rows = []
        for table_row in soup.findAll('tr'):
            columns = table_row.findAll('td')
            output_row = []
            for column in columns:
                output_row.append(column.text)
            output_rows.append(output_row)

        df = pd.DataFrame(data=output_rows)
        df.to_csv('GAoutput.csv', sep=',', encoding='utf_8_sig',index=0)
        return 'OK'
    if request.method == 'GET':
        return send_from_directory("./", 'GAoutput.csv', as_attachment=True)
if __name__ == "__main__":
    app.secret_key = os.urandom(12)

    app.run(host='0.0.0.0',port=80,threaded=True)