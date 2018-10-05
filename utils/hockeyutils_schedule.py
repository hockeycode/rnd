# Schedule information from the NHL API
# 1. Collect the list of games for a single season
# 2. Collect the list of games over multiple seasons
# 3. Pull the list of games for a given team from existing data

import pandas as pd
import numpy as np 
import json
import hockeyutils2 as h

####################################################################
# 1. Collect the list of games for a single season
####################################################################
def schedulesingleseason(outloc,apiurl,season):

	thisurl=apiurl+'/schedule?startDate='+repr(season)[0:4]+'-07-01&endDate='+repr(season)[4:8]+'-06-30'
	r=h.pulldown(inurl=thisurl)

	# format data and create the index
	df = pd.io.json.json_normalize(r['dates'],['games'])
	df.rename(index=str, columns={'gamePk': 'gameid'},inplace=True)
	df.set_index('gameid',inplace=True)

	# get team information in there
	df2=h.flatten(df,'teams',stem='t.')
	dfa=h.flatten(df2,'t.away',stem='a.')
	dfa2=h.flatten(dfa,'a.leagueRecord',stem='a.lr.')
	dfh=h.flatten(df2,'t.home',stem='h.')
	dfh2=h.flatten(dfh,'h.leagueRecord',stem='h.lr.')
	df=df.join([dfa,dfa2,dfh,dfh2], how='outer')
	df.drop(columns=['teams','h.leagueRecord','a.leagueRecord'],inplace=True)

	# get venue information
	dfv=h.flatten(df,'venue',stem='v.')
	df=df.join(dfv,how='outer')
	df.drop(columns=['venue'],inplace=True)

	# drop content and status since they are not useful
	df.drop(columns=['content','status'],inplace=True)

	return(df)

####################################################################
# 2. Collect the list of games over multiple seasons
#    Note that this doesn't have to be season-based, but the rest
#    of my analysis IS season-based, so I'm going with it
####################################################################
def schedulemultiseason(outloc,apiurl,seasons):
	
	slist=[]
	for season in seasons:
		df=schedulesingleseason(outloc,apiurl,season)
		slist.append(df)

	dfs=pd.concat(slist,keys=seasons,names=['season','gameid'],sort=True)
	
	return(dfs)

