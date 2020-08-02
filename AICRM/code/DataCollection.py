# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, TIMESTAMP,DateTime, Integer,create_engine
from sqlalchemy.ext.declarative import declarative_base
from collections import OrderedDict
from sqlalchemy_utils import database_exists, create_database
import datetime
Base = declarative_base() # create ORM converter
LS = 'mysql+pymysql://root:rootroot@127.0.0.1/DataFilter?charset=utf8mb4'
engine = create_engine(LS, encoding='utf-8', pool_recycle = True)  # Link to database
# 動態建立資料庫
if not database_exists(engine.url):
    create_database(engine.url)

# 儲存轉換模組轉換欄位名稱
class ColumnMapping(Base):
    __tablename__ = "ColumnMapping"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    defColumn = Column(String(40))
    Vendor = Column(String(40))
    FileName = Column(String(40))
    VendorColumn = Column(String(40))
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("defColumn", self.defColumn), 
            ("Vendor", self.Vendor),       
            ("FileName", self.FileName),            
            ("VendorColumn", self.VendorColumn)
        ])
        return jsonObj

# 已上傳檔案
class UploadFile(Base):
    __tablename__ = "UploadFile"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    FileName = Column(String(100))
    Vendor = Column(String(40))
    FileFrom = Column(String(100))
    FileTime_start = Column(DateTime)
    FileTime_end = Column(DateTime)
    Number = Column(Integer())
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("FileName", self.FileName), 
            ("Vendor", self.Vendor),            
            ("FileFrom", self.FileFrom),
            ("FileTime_start", (self.FileTime_start).strftime("%Y/%m/%d")),
            ("FileTime_end", (self.FileTime_end).strftime("%Y/%m/%d")),
            ("Number", self.Number)
        ])
        return jsonObj

# 已篩選檔案
class FilterFile(Base):
    __tablename__ = "FilterFile"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    FileName = Column(String(100))
    FromUploadFileName = Column(String(100))
    Vendor = Column(String(40))
    FileFrom = Column(String(100))
    FileTime_start = Column(DateTime)
    FileTime_end = Column(DateTime)
    FilterContent = Column(String(1000))
    Number = Column(Integer())
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("no", self.no), 
            ("FileName", self.FileName), 
            ("FromUploadFileName", self.FromUploadFileName), 
            ("Vendor", self.Vendor),            
            ("FileFrom", self.FileFrom),
            ("FileTime_start", (self.FileTime_start).strftime("%Y/%m/%d")),
            ("FileTime_end", (self.FileTime_end).strftime("%Y/%m/%d")),
            ("FilterContent", self.FilterContent),
            ("Number", self.Number)
        ])
        return jsonObj
# 簡訊模組檔案
class MessageFile(Base):
    __tablename__ = "MessageFile"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    FileName = Column(String(100))
    FromUploadFileName = Column(String(100))
    Vendor = Column(String(40))
    CreateTime = Column(DateTime, default=datetime.datetime.now)
    Status = Column(String(40), default=u'創建中...')
    FileFrom = Column(String(100))
    FileTime_start = Column(DateTime)
    FileTime_end = Column(DateTime)
    Medium = Column(String(40))
    Campaign = Column(String(40))
    Content = Column(String(400))
    OriginalFileName = Column(String(40))
    Number = Column(Integer())
    SendStatus = Column(String(40), default=u'尚未寄送')

    def convert_Json(self):
        jsonObj = OrderedDict([
            ("FileName", self.FileName), 
            ("FromUploadFileName", self.FromUploadFileName), 
            ("Vendor", self.Vendor),            
            ("CreateTime", self.CreateTime),
            ("Status", self.Status),
            ("FileFrom", self.FileFrom),
            ("FileTime_start", (self.FileTime_start).strftime("%Y/%m/%d")),
            ("FileTime_end", (self.FileTime_end).strftime("%Y/%m/%d")),
            ("Medium", self.Medium),
            ("Campaign", self.Campaign),
            ("Number", self.Number),
            ("SendStatus", self.SendStatus),

            ("Content", self.Content),
            ("OriginalFileName", self.OriginalFileName)
        ])
        return jsonObj

# 已寄送之簡訊狀態、GA成效紀錄
class SendMessageResult(Base):
    __tablename__ = "SendMessageResult"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    Vendor = Column(String(40))
    FileName = Column(String(100))
    SendTime = Column(DateTime, default=datetime.datetime.now)
    MessageFileName = Column(String(100))
    MessageStatus_finish = Column(Integer())
    MessageStatus_reservation = Column(Integer())
    MessageStatus_timeout = Column(Integer())
    MessageStatus_error = Column(Integer())
    GA_Click = Column(Integer())
    GA_TransactionTimes = Column(Integer())
    GA_Revenue = Column(Integer())
    Number = Column(Integer())
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("no", self.no),  
            ("Vendor", self.Vendor),            
            ("FileName", self.FileName),
            ("SendTime", self.SendTime),
            ("MessageFileName", self.MessageFileName), 
            ("MessageStatus_finish", self.MessageStatus_finish),
            ("MessageStatus_reservation", self.MessageStatus_reservation),
            ("MessageStatus_timeout", self.MessageStatus_timeout),
            ("MessageStatus_error", self.MessageStatus_error),
            ("Number", self.Number),
            ("GA_Click", self.GA_Click),            
            ("GA_TransactionTimes", self.GA_TransactionTimes),
            ("GA_Revenue", self.GA_Revenue),
        ])
        return jsonObj

# AI篩選檔案
class AIfilterFile(Base):
    __tablename__ = "AIfilterFile"
    no = Column(Integer(), primary_key=True ,autoincrement=True)
    FileName = Column(String(100))
    Vendor = Column(String(40))
    CreateTime = Column(DateTime, default=datetime.datetime.now)
    Number = Column(Integer())
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("FileName", self.FileName),  
            ("Vendor", self.Vendor),            
            ("CreateTime", self.CreateTime),
            ("Number", self.Number)
        ])
        return jsonObj
# 使用者帳戶
class Account(Base):
    __tablename__ = "Account"
    Account = Column(String(45), primary_key=True)
    Password = Column(String(45))
    def convert_Json(self):
        jsonObj = OrderedDict([
            ("Account", self.Account), 
            ("Password", self.Password)
        ])
        return jsonObj

Base.metadata.create_all(engine)


