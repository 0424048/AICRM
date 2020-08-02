# -*- coding: UTF-8 -*-
import pandas as pd
import datetime as dt
from lifetimes import BetaGeoFitter
from lifetimes.plotting import *
from lifetimes.utils import *
from lifetimes import GammaGammaFitter
import numpy as np

today = dt.date.today()
i=0
def flag_df(df):

    if (df['level'] =='A'):
        return 1
    elif (df['level'] =='B'):
        return 0.8
    elif (df['level'] =='C'):
        return 0.6
    elif df['level'] == np.nan:
        return 1
def ga_toLevel(df):
    if (df['level'] ==u'點擊未購買'):
        return 'B'
    elif (df['level'] ==u'尚未點擊'):
        return 'C'
    elif (df['level'] >= 0):
        return 'A'
    elif df['level'] == np.nan:
        return 'A'
def time_df(df):
    global i

    if(df['cycle']>0):
       i+=1
       return pd.DateOffset(days=df['cycle'])
    else:
       return np.nan
def predicted_purchase_time(account,timesteap):
  # df = pd.read_csv('AIexcel/' + account + '.csv' , sep=',', names=['name','uuid','invoiceDate','produce_name','Total'],encoding='utf8',low_memory=False)
  df = pd.read_csv('AIexcel/' + account + '.csv',names=['name','uuid','invoiceDate','produce_name','Total'], sep=',',encoding='utf8',low_memory=False)
  #df.rename(columns={u'收件人姓名':u'name', u'收件人手機':u'uuid', u'付款日期':u'invoiceDate', u'商品名稱':u'produce_name', u'商品總價':u'Total'}, inplace=True)
  df_ga = pd.read_csv('AIexcel/' + account + '_ga.csv' , names=['uuid','level','next_time'],sep=',',encoding='utf8',low_memory=False)
  df_UserLabel = df_ga['level'][1:].tolist()
  df_ga.drop([0],inplace=True)
  if 'level' in df_ga:
    df_ga['level'] = df_ga.apply(ga_toLevel, axis = 1)
  df = df.dropna()
  df = df.ix[df.Total.str.isnumeric()]
  df = df.ix[df.invoiceDate.str.len() ==19]
  df = df.ix[df.name.str.len() <=10]
  # take three columns
  df1 = df[['uuid','invoiceDate','Total']]
  # drop price == 1
  df1_ = df1.drop(df1[df1['invoiceDate'] == 1].index)
  # drop non-data
  df_drop = df1_.dropna()
  # change columns name
  dataframe = df_drop
  dataframe['invoiceDate'] = pd.to_datetime(dataframe['invoiceDate']).dt.date
  dataframe.Total = dataframe.Total.astype(float)
  data = summary_data_from_transaction_data(dataframe,
                                'uuid',
                                'invoiceDate',
                                 observation_period_end=dataframe.invoiceDate.max())
  data2 = summary_data_from_transaction_data(dataframe,
                              'uuid',
                              'invoiceDate',
                              monetary_value_col='Total',
                              observation_period_end=dataframe.invoiceDate.max())


  bgf = BetaGeoFitter(penalizer_coef=0.01)
  bgf.fit(data['frequency'], data['recency'], data['T'])
  purchase_time = data
  purchase_time['predicted_purchases'] = bgf.conditional_expected_number_of_purchases_up_to_time(timesteap,
                                                data['frequency'],
                                                data['recency'],
                                                data['T'])
  predicted_purchases_df = purchase_time[['predicted_purchases']].sort_values(by='predicted_purchases',ascending=False)
  predicted_purchases_df['cycle'] = data['recency']/data['frequency']
  returning_customers_summary = data2[ (data2['frequency'] > 0) &
                                     (data2['monetary_value'] != 0)]
  ggf = GammaGammaFitter(penalizer_coef = 0.001)
  ggf.fit(returning_customers_summary['frequency'],
        returning_customers_summary['monetary_value'])
  income = ggf.conditional_expected_average_profit(
        returning_customers_summary['frequency'],
        returning_customers_summary['monetary_value']
      ).to_frame()
  income.columns = ['predicted_price']
  predicted_purchases_df = predicted_purchases_df.merge(income, on=['uuid'],how='left')
  predicted_purchases_df.reset_index(inplace=True)

  mask = predicted_purchases_df.predicted_purchases > 1
  predicted_purchases_df.loc[mask, 'predicted_purchases'] = 1
  predicted_purchases_df['predicted_purchases'] = predicted_purchases_df['predicted_purchases'].astype(float)
  predicted_purchases_df = predicted_purchases_df.sort_values(by=['predicted_purchases'], ascending=False)
  predicted_purchases_df['predicted_purchases'] = predicted_purchases_df['predicted_purchases'].apply(lambda x: format(x, '.2%'))

  predicted_purchases_df=predicted_purchases_df.merge(df_ga,left_on="uuid",right_on="uuid",how='left')

  predicted_purchases_df['level'] = predicted_purchases_df.apply(flag_df, axis = 1)
  #predicted_purchases_df['level'] = predicted_purchases_df['level'].fillna(1)
  predicted_purchases_df.replace(np.nan, 0, inplace=True)
  predicted_purchases_df.replace(np.inf, 0, inplace=True)
  if 'next_time' not in predicted_purchases_df.columns:
    predicted_purchases_df['next_time'] = np.nan
  predicted_purchases_df['next_time'] =  pd.to_datetime(predicted_purchases_df['next_time'])

  predicted_purchases_df_N = predicted_purchases_df[~(predicted_purchases_df.uuid.isin(((predicted_purchases_df[predicted_purchases_df.next_time>=today].uuid).astype(str)).tolist()))]
  predicted_purchases_df_off = predicted_purchases_df[(predicted_purchases_df.uuid.isin(((predicted_purchases_df[predicted_purchases_df.next_time>=today].uuid).astype(str)).tolist()))]
  new_df = predicted_purchases_df_N.append(predicted_purchases_df_off, ignore_index=True)
  predicted_purchases_df_N['cycle'] = (predicted_purchases_df_N['cycle']*predicted_purchases_df_N['level']).round(0).astype(int)
  predicted_purchases_df_N['next_time'] = today+predicted_purchases_df_N.apply(time_df, axis = 1)
  predicted_purchases_df_NQ = predicted_purchases_df_N.dropna()
  predicted_purchases_df_off = predicted_purchases_df_off.drop(columns=['predicted_purchases','cycle','predicted_price'])
  predicted_purchases_df_NQ = predicted_purchases_df_NQ.drop(columns=['predicted_purchases','cycle','predicted_price'])
  df_ga=df_ga.merge(predicted_purchases_df_off,left_on="uuid",right_on="uuid",how='left')
  df_ga=df_ga.merge(predicted_purchases_df_NQ,left_on="uuid",right_on="uuid",how='left')
  notNull_df = df_ga[df_ga['level'].notnull() & df_ga['next_time'].notnull()].drop(columns=['level_y','next_time_y','next_time_x','level_x'])
  notNull_df2 = df_ga[df_ga['level_y'].notnull() & df_ga['next_time_y'].notnull()].drop(columns=['level','next_time','next_time_x','level_x'])
  notNull_df2.columns = ['uuid','level','next_time']
  res = pd.concat([notNull_df,notNull_df2],axis=0, ignore_index=True)
  res.rename(columns={u'uuid':u'收件人手機'}, inplace=True)
  res['UserLabel'] = pd.Series(df_UserLabel)
  res = res[[u'收件人手機',u'UserLabel',u'next_time']]
  res.to_csv('AIexcel/' + account + '_ga.csv',index=False,encoding='utf8')
  predicted_purchases_df_N = predicted_purchases_df_N.drop(columns=['level','cycle','next_time'])
  predicted_purchases_df_N.columns = [u'收件人手機',u'顧客購買機率',u'平均交易金額']

  return predicted_purchases_df_N
#print(predicted_purchase_time('666666',30)[:30])