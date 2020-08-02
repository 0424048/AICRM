df = pd.read_csv('uploadExl/14fb6e8dd2a1498585fc06712c3d61f9.csv' , sep=',', encoding='utf_8_sig',low_memory=False)


df[u'訂單日期'] = pd.to_datetime(df[u'訂單日期'],errors='coerce')
df = df[pd.notnull(df[u'訂單日期'])]
df.groupby([u'收件人手機']).filter(lambda x: (x[u'訂單日期'].astype(dtype='datetime64',errors='ignore') > datetime.datetime.now() - datetime.timedelta(days=int(c))).any())[u'收件人手機'].values.tolist()



pd.to_datetime(dff[u'訂單日期'],errors='ignore')

dff[u'訂單日期'] = pd.to_datetime(dff[u'訂單日期'],errors='coerce')


dff = dff[pd.notnull(df[u'訂單日期'])]

df[u'訂單日期'] = pd.to_datetime(df[u'訂單日期'],errors='ignore')


dff = pd.DataFrame({u'訂單日期': ['9/13/16 17:59', '9/14/16 21:34',u'哈哈哈哈'],
                    u'名字': [u'對的', u'也是對的',u'噠噠'],
                    u'收件人手機': ['0977', '0978','7878']})





saveCell = df.groupby([u'收件人手機']).filter(lambda x: (x[item].astype('object').str.contains(filterValue)).any())[u'收件人手機'].values.tolist()

f = df[df[u'收件人手機'].isin(saveCell) == True]

df = pd.read_csv('/uploadExl/0a2ce8407d52400ea3b500706e4e2572.csv' , sep=',', encoding='utf_8_sig',low_memory=False)

df = pd.read_csv('0978136278.csv' , sep=',', encoding='utf_8_sig',low_memory=False)

errors = ""

errorsList = df.loc[~df[u'收件人姓名'].astype('unicode').str.isdigit(), u'收件人手機'].tolist()
for idx,e in enumerate(errorsList):
	in_row = df[df[u'收件人手機']==e].index[0]
	errors = errors + e
	if idx != 0:
		errors+= ''
print errors