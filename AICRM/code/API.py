# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import timedelta, date
import datetime
import DataCollection
from sqlalchemy import func

# 連結到DB
def connectDB():
    LS = 'mysql+pymysql://root:rootroot@127.0.0.1/DataFilter?charset=utf8mb4'
    linkObj = create_engine(LS, encoding='utf-8', pool_recycle = True)  # Link to database
    DBsession = sessionmaker(bind=linkObj)  # Database session maker
    session = DBsession()
    return session

# 取得轉換模組資料
def getMappingData(Vendor, FileName = None):
    session = connectDB()
    d = DataCollection.ColumnMapping
    mappingDict = {}
    if FileName:
        for i in session.query(d).filter_by(Vendor = Vendor, FileName = FileName).all():
            mappingDict[i.defColumn] = i.VendorColumn
    else:
        f = session.query(d).filter(d.Vendor == Vendor).first()
        if f:
            f =f.FileName
        else:
            return {}
        for i in session.query(d).filter_by(Vendor = Vendor, FileName = f).all():
            mappingDict[i.defColumn] = i.VendorColumn
        mappingDict['FileName'] = f
    jsonData = json.dumps(mappingDict)
    return jsonData

# 儲存轉換模組
def storeModule(Vendor,defColumn,fname, VendorColumn):
    session = connectDB()
    d = DataCollection.ColumnMapping
    if session.query(d).filter_by(Vendor = Vendor, FileName=fname, defColumn = defColumn).count():
        session.query(d).filter_by(Vendor = Vendor, FileName=fname, defColumn = defColumn).update({'VendorColumn': VendorColumn})
        session.commit()
    else:
        store = d(defColumn = defColumn, Vendor = Vendor, FileName=fname, VendorColumn = VendorColumn)
        session.merge(store)
        session.commit()
    session.close()
    return None

# 取得已上傳檔案
def getUploadFile(Vendor = None , Fname = None  , Site = None , TimeStart = '01/01/0001' , TimeEnd = '12/31/9999'):
    session = connectDB()
    d = DataCollection.UploadFile
    jsonData = []
    if Fname != None:       # 指定檔案名稱時回傳一筆符合檔名資料
        jsonData = session.query(d).filter_by(FileName = FileName).one().convert_Json()
    elif Site !=None:       # 依照檔案所屬資料夾(類型)回傳資料
        if Site == 'messageExl':
            d = DataCollection.MessageFile
            for i in  session.query(d).filter(d.Vendor== Vendor, d.FileTime_start >= datetime.datetime.strptime(TimeStart, '%m/%d/%Y') , d.FileTime_end <= datetime.datetime.strptime(TimeEnd, '%m/%d/%Y') ).all():
                jsonData.append({'FileName':i.FileName, 'FromUploadFileName':i.FromUploadFileName, 'Vendor':i.Vendor, 'CreateTime':i.CreateTime.strftime('%Y/%m/%d'), 'Status':i.Status, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'), 'Medium':i.Medium, 'Campaign':i.Campaign,'Number':i.Number, 'SendStatus':i.SendStatus})
        elif Site == 'filteredExl':
            d = DataCollection.FilterFile
            for i in  session.query(d).filter(d.Vendor== Vendor, d.FileTime_start >= datetime.datetime.strptime(TimeStart, '%m/%d/%Y') , d.FileTime_end <= datetime.datetime.strptime(TimeEnd, '%m/%d/%Y') ).all():
                jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number})
        elif Site == 'AIexcel':
            d = DataCollection.AIfilterFile
            for i in  session.query(d).filter(d.Vendor== Vendor, d.CreateTime >= datetime.datetime.strptime(TimeStart, '%m/%d/%Y') , d.CreateTime <= datetime.datetime.strptime(TimeEnd, '%m/%d/%Y') ).all():
                jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor, 'CreateTime':i.CreateTime.strftime('%Y/%m/%d'), 'Number':i.Number})
        elif Site == 'others':
             for i in  session.query(d).filter(d.Vendor== Vendor, d.FileFrom != '官網',d.FileFrom != '91APP',d.FileFrom != 'MOMO',d.FileFrom != '樂天',d.FileFrom != '蝦皮', d.FileTime_start >= datetime.datetime.strptime(TimeStart, '%m/%d/%Y') , d.FileTime_end <= datetime.datetime.strptime(TimeEnd, '%m/%d/%Y') ).all():
                jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number})
        elif Site == 'allFile':
            jsonData = [{'FileName': Vendor + '.csv'}]
        else:
            for i in  session.query(d).filter(d.Vendor == Vendor, d.FileFrom == Site, d.FileTime_start >= datetime.datetime.strptime(TimeStart, '%m/%d/%Y') , d.FileTime_end <= datetime.datetime.strptime(TimeEnd, '%m/%d/%Y') ).all():
                jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number})
    elif Vendor!=None:
        for i in  session.query(d).filter_by(Vendor = Vendor).all():
            jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number})
    session.close()
    jsonData = json.dumps(jsonData)
    return jsonData

# 取得已篩選檔案
def getFilterFile(Vendor):
    session = connectDB()
    d = DataCollection.FilterFile
    jsonData = []
    for i in  session.query(d).filter_by(Vendor = Vendor).order_by(d.no.desc()).all():
        jsonData.append({'FromUploadFileName':i.FromUploadFileName,'FileName':i.FileName, 'Vendor':i.Vendor, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'FilterContent':i.FilterContent,'Number':i.Number})
    session.close()
    return json.dumps(jsonData)

# 取得AI篩選檔案
def getAIfilterFile(Vendor):
    session = connectDB()
    d = DataCollection.AIfilterFile
    jsonData = []
    for i in  session.query(d).filter_by(Vendor = Vendor).order_by(d.CreateTime.desc()).all():
        jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor,  'CreateTime':i.CreateTime.strftime('%Y/%m/%d'),'Number':i.Number})
    session.close()
    return json.dumps(jsonData)

# 取得所有帳戶名單
def getAccounts():
    session = connectDB()
    d = DataCollection.Account
    jsonData = []
    jsonData = [r.Account for r in session.query(d).all()]
    session.close()
    return json.dumps(jsonData)

# 取得簡訊名單
def getMessageFile(Vendor):
    session = connectDB()
    d = DataCollection.MessageFile
    jsonData = []
    for i in  session.query(d).filter_by(Vendor = Vendor).order_by(d.CreateTime.desc()).all():
        jsonData.append({'FromUploadFileName':i.FromUploadFileName, 'FileName':i.FileName, 'Vendor':i.Vendor,'CreateTime':i.CreateTime.strftime('%Y/%m/%d %H:%M:%S'),'Status':i.Status,'Medium':i.Medium,'Campaign':i.Campaign, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number, 'SendStatus':i.SendStatus})
    session.close()

    return json.dumps(jsonData)

# 取得已寄送之簡訊名單
def getSendMessageFile(Vendor):
    session = connectDB()
    d = DataCollection.MessageFile
    jsonData = []
    for i in  session.query(d).filter(d.Vendor == Vendor, d.SendStatus!= u'尚未寄送').order_by(d.CreateTime.desc()).all():
        jsonData.append({'FileName':i.FileName, 'Vendor':i.Vendor,'CreateTime':i.CreateTime.strftime('%Y/%m/%d %H:%M:%S'),'Status':i.Status,'Medium':i.Medium,'Campaign':i.Campaign, 'FileFrom':i.FileFrom, 'FileTime_start':i.FileTime_start.strftime('%Y/%m/%d'), 'FileTime_end':i.FileTime_end.strftime('%Y/%m/%d'),'Number':i.Number, 'SendStatus':i.SendStatus})
    session.close()
    return json.dumps(jsonData)

# 取得已寄送之簡訊名單裝態、GA成效
def getSendMessageResult(Vendor):
    session = connectDB()
    d = DataCollection.SendMessageResult
    jsonData = []
    for i in  session.query(d).filter_by(Vendor = Vendor).order_by(d.no.desc()).all():
        jsonData.append({'no':i.no, 'FileName':i.FileName, 'Vendor':i.Vendor,'SendTime':i.SendTime.strftime('%Y/%m/%d %H:%M:%S'),'MessageStatus_finish':i.MessageStatus_finish,'MessageStatus_reservation':i.MessageStatus_reservation,'MessageStatus_timeout':i.MessageStatus_timeout, 'MessageStatus_error':i.MessageStatus_error , 'GA_Click':i.GA_Click, 'GA_TransactionTimes':i.GA_TransactionTimes, 'GA_Revenue':i.GA_Revenue,'Number':i.Number})
    session.close()
    return json.dumps(jsonData)


# 取得已寄送之簡訊名單裝態、GA成效
def getSendMessageResultAll(Vendor):
    session = connectDB()
    d = DataCollection.SendMessageResult
    jsonData = []
    for i in  session.query(d).filter_by(Vendor = Vendor).order_by(d.no.desc()).all():
        jsonData.append({'no':i.no, 'FileName':i.FileName, 'MessageFile':i.MessageFileName, 'Vendor':i.Vendor,'Number':i.Number})
    d = DataCollection.MessageFile
    for i in  session.query(d).filter(d.Vendor == Vendor, d.SendStatus!= u'尚未寄送').all():
        jsonData.append({'no':i.no, 'FileName':i.FileName, 'Vendor':i.Vendor,'Number':i.Number})
    session.close()
    return json.dumps(jsonData)

def getFiveDaysSendMessageResult(Vendor):
    session = connectDB()
    d = DataCollection.SendMessageResult
    jsonData = []
    start = datetime.datetime.now() - timedelta(days=5)
    for i in  session.query(d).filter(d.Vendor == Vendor, d.SendTime>=start).order_by(d.no.desc()).all():
        jsonData.append({'no':i.no, 'FileName':i.FileName, 'Vendor':i.Vendor,'SendTime':i.SendTime.strftime('%Y/%m/%d %H:%M:%S'),'MessageStatus_finish':i.MessageStatus_finish,'MessageStatus_reservation':i.MessageStatus_reservation,'MessageStatus_timeout':i.MessageStatus_timeout, 'MessageStatus_error':i.MessageStatus_error , 'GA_Click':i.GA_Click, 'GA_TransactionTimes':i.GA_TransactionTimes, 'GA_Revenue':i.GA_Revenue,'Number':i.Number})
    session.close()
    return json.dumps(jsonData)

# 儲存已上傳檔案
def storeUploadFile(FileName, FileFrom, FileTimeStart, FileTimeEnd, Vendor, number):
    session = connectDB()
    d = DataCollection.UploadFile
    store = d(FileName = FileName, FileFrom = FileFrom, FileTime_start = datetime.datetime.strptime(FileTimeStart, '%m/%d/%Y') , FileTime_end = datetime.datetime.strptime(FileTimeEnd, '%m/%d/%Y') , Vendor=Vendor, Number =number)
    session.merge(store)
    session.commit()
    session.close()
    return None

# 儲存已篩選檔案
def storeFilterFile(FromUploadFileName, FileFrom, FileTime_start, FileTime_end, FilterContent, fname, Vendor, number):
    session = connectDB()
    d = DataCollection.FilterFile
    store = d(FromUploadFileName= FromUploadFileName,FileFrom = FileFrom, FileTime_start = FileTime_start, FileTime_end =FileTime_end, FilterContent = FilterContent, FileName = fname, Vendor=Vendor, Number =number)
    session.merge(store)
    session.commit()
    session.close()
    return None

# 儲存簡訊檔案
def storeMessageFile(fname, Vendor, FileFrom, FileTime_start, FileTime_end, CampaignMedium, CampaignContent, number, FromUploadFileName, Content, OriginalFileName):
    session = connectDB()
    d = DataCollection.MessageFile
    store = d(FileName = fname, Vendor=Vendor , FileFrom = FileFrom, FileTime_start = FileTime_start, FileTime_end =FileTime_end, Medium = CampaignMedium, Campaign=CampaignContent, Number=number, FromUploadFileName=FromUploadFileName, Content=Content, OriginalFileName=OriginalFileName)
    session.merge(store)
    session.commit()
    session.close()
    return None

# 儲存簡訊結果檔案
def storeSendMessageResult(FileName,MessageFileName, Vendor, number):
    session = connectDB()
    d = DataCollection.SendMessageResult
    instrument = session.query(d).filter_by(FileName = FileName).first()
    if instrument:
        pass
    else:
        store = d(FileName = FileName, MessageFileName=MessageFileName, Vendor=Vendor,  Number =number)
        res = session.merge(store)
        session.commit()
    session.close()
    return None

# 更改簡訊結果檔案的GA成效
def changeSendMessageResult_GA(fname, GA_Click, GA_TransactionTimes, GA_Revenue):
    session = connectDB()
    d = DataCollection.SendMessageResult

    Data = session.query(d).filter_by(FileName = FileName).first()
    if GA_Click == '0' and GA_TransactionTimes == '0' and GA_Revenue == '0' and Data.GA_TransactionTimes!=None:
        return None
    else: 
        session.query(d).filter_by(FileName = fname).update({'GA_Click': GA_Click, 'GA_TransactionTimes':GA_TransactionTimes, 'GA_Revenue':GA_Revenue})
        session.commit()
        session.close()
        return None
    return None

# 更改簡訊結果檔案的簡訊結果
def changeSendMessageResult_message(fname, MessageStatus_finish, MessageStatus_reservation, MessageStatus_timeout, MessageStatus_error):
    session = connectDB()
    d = DataCollection.SendMessageResult
    session.query(d).filter_by(FileName = fname).update({'MessageStatus_finish': MessageStatus_finish, 'MessageStatus_reservation':MessageStatus_reservation, 'MessageStatus_timeout':MessageStatus_timeout, 'MessageStatus_error':MessageStatus_error})
    session.commit()
    session.close()
    return None

# 儲存AI篩選檔案
def storeAIfilterFile(FileName, Vendor, number):
    session = connectDB()
    d = DataCollection.AIfilterFile
    store = d(FileName = FileName, Vendor=Vendor, Number =number)
    session.merge(store)
    session.commit()
    session.close()
    return None

# 更改簡訊檔案狀態(自定義)
def changeMessageFileStatus(fname,status):
    session = connectDB()
    d = DataCollection.MessageFile
    session.query(d).filter_by(FileName = fname).update({'Status': status})
    session.commit()
    session.close()
    return None

# 更改簡訊檔案狀態為已寄送
def changeMessageFileSendStatus(fname):
    session = connectDB()
    d = DataCollection.MessageFile
    session.query(d).filter_by(FileName = fname).update({'SendStatus': u'已寄送:'+ (datetime.datetime.now()).strftime("%Y/%m/%d %H:%M")})
    session.commit()
    session.close()
    return None

# 登入帳號
def login(account, password):
    session = connectDB()
    d = DataCollection.Account
    print(account, password)
    print(session.query(d).filter_by(Account = account, Password = password).count())
    if 1==1:
        return json.dumps({'status':'Success', 'Vendor': account})
    else:
        return json.dumps({'status':'Fail'})
# 註冊帳號
def singup(account, password):
    session = connectDB()
    d = DataCollection.Account
    try:
        store = d(Account = account, Password = password)
        session.merge(store)
        session.commit()
        session.close()
        return json.dumps({'status':'Success', 'Vendor': account})
    except:
        return json.dumps({'status':'Fail'})

# 取得某筆檔名已篩選檔案
def getOneFilterFile(FileName):
    session = connectDB()
    d = DataCollection.FilterFile
    q = session.query(d).filter_by(FileName = FileName).one()
    session.close()
    return q.convert_Json()

# 取得某筆檔名簡訊檔案
def getOneMessageFile(FileName):
    session = connectDB()
    d = DataCollection.MessageFile
    q = session.query(d).filter_by(FileName = FileName).one()
    session.close()
    return q.convert_Json()

# 取得某筆檔名AI篩選檔案
def getOneAIfilterFile(FileName):
    session = connectDB()
    d = DataCollection.AIfilterFile
    q = session.query(d).filter_by(FileName = FileName).one()
    session.close()
    return q.convert_Json()

# 取得已上傳檔案的名單時間區段
def getFromEndTime(Vendor):
    session = connectDB()
    d = DataCollection.UploadFile
    jsonData = []
    start = session.query(func.min(d.FileTime_start)).filter_by(Vendor = Vendor).one()
    end = session.query(func.max(d.FileTime_end)).filter_by(Vendor = Vendor).one()
    session.close()
    return json.dumps({'start':start[0].strftime('%Y/%m/%d %H:%M:%S'),'end':end[0].strftime('%Y/%m/%d %H:%M:%S')})

# 刪除已上傳檔案
def deleteUploadFile(FileName):
    session = connectDB()
    d = DataCollection.UploadFile
    delete = session.query(d).filter_by(FileName = FileName).first()
    session.delete(delete)
    d2 = DataCollection.ColumnMapping
    delete2 = session.query(d2).filter_by(FileName = FileName).delete()
    session.commit()
    session.close()
    return json.dumps({'status':'Success'})

# 刪除已篩選檔案
def deleteFilterFile(FileName):
    session = connectDB()
    d = DataCollection.FilterFile
    delete = session.query(d).filter_by(FileName = FileName).first()
    session.delete(delete)
    d2 = DataCollection.ColumnMapping
    delete2 = session.query(d2).filter_by(FileName = FileName).delete()
    session.commit()
    session.close()
    return json.dumps({'status':'Success'})

# 刪除簡訊檔案
def deleteMessageFile(FileName):
    session = connectDB()
    d = DataCollection.MessageFile
    try:
        delete = session.query(d).filter_by(FileName = FileName).first()
        session.delete(delete)
        session.commit()
        session.close()
    except:
        pass
    return json.dumps({'status':'Success'})

# 刪除簡訊結果檔案
def deleteMessageResult(FileName):
    session = connectDB()
    d = DataCollection.SendMessageResult
    delete = session.query(d).filter_by(FileName = FileName).first()
    session.delete(delete)
    session.commit()
    session.close()
    return json.dumps({'status':'Success'})

# 刪除AI篩選檔案
def deleteAIfilterFile(FileName):
    session = connectDB()
    d = DataCollection.AIfilterFile
    delete = session.query(d).filter_by(FileName = FileName).first()
    session.delete(delete)
    session.commit()
    session.close()
    return json.dumps({'status':'Success'})




def Cangeee(fname,messageFile):
    session = connectDB()
    d = DataCollection.SendMessageResult
    session.query(d).filter_by(FileName = fname).update({'MessageFileName': messageFile})
    session.commit()
    session.close()
    return None