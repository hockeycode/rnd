# Useful things for working with the NHL API
# 1. This is a json data pull utility that lets you pull data 
#    from a url or from a local file with a common interface
#    Convenient for debugging
# 2. extract a primary key hidden deep in your json 
# 3. flatten a df column that contains a dictionary 

import requests
import pandas as pd
import numpy as np 
import json
import codecs


####################################################################
# 1. This is a json data pull utility that lets you pull data 
#    from a url or from a local file with a common interface
#    This should let you:
#        (a) for data not currently available locally, pull it from
#            a url
#        (b) for data not currently available locally, store it in
#            a specified file
#        (c) for data currently available locally, pull it from that 
#            file
#    Convenient for debugging
####################################################################

def pulldown(inurl='',outfile=''):
	# Requires: codecs, requests, json
	# Assumes: inurl is in utf-8 format
	if inurl != '':
		#print(inurl)

		s = requests.Session()
		a = requests.adapters.HTTPAdapter(max_retries=3)
		b = requests.adapters.HTTPAdapter(max_retries=3)
		s.mount('http://', a)
		s.mount('https://', b)
		r=s.get(inurl)

		#r=requests.get(inurl)
		if outfile != '':
			f=codecs.open(outfile,'w',encoding='utf-8')
			json.dump(r.json(),f,indent=4,encoding='utf-8',ensure_ascii=False)
		return(r.json())
	else:
		if outfile != '':
			with open(outfile, 'r') as json_file:
				r = json.load(json_file)
		else:
			r={}
		return(r)



####################################################################
# 2. extract a primary key hidden deep in your json 
#    This may need to be applied multiple times to uncover a
#    primary key hidden very deep down
####################################################################
def indextract(df,indloc,itype='n'):
	# suppose your primary key (or part of it) is hiding deep
	# in some json -- pull that out
	newcol=indloc[0]+'.'+indloc[1]
	if itype=='c':
		df[newcol]=''
	else:
		df[newcol]=np.nan

	for ii in range(df.shape[0]):
		df.iloc[ii,df.columns.get_loc(newcol)]=df.iloc[ii,df.columns.get_loc(indloc[0])][indloc[1]]
	return(df)


####################################################################
# 3. flatten a df column that contains a dictionary  
#    An alternative to json_normalize when that one fails
####################################################################
def flatten(df,dictcol,stem='',skip=[]):
	if stem=='':
		stem=dictcol+'.'
	newdf=pd.DataFrame(df[dictcol].tolist(),index=df.index)
	for c in newdf.columns:
		if c in skip:
			newdf.drop(columns=[c],inplace=True)
		else:
			newdf.rename(columns={c: stem+c},inplace=True)
	return(newdf)









