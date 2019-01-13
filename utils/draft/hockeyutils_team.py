# Team-level information from the NHL API
# 1. Collect stats for all teams for a given season
# 2. Generic load of json single-season stats data from a 
#    local json file
# 3. Generic load of json conference, location, and franchise data
# 4. Pull teamstats for an arbitrary list of seasons
import pandas as pd
import numpy as np 
import json
import hockeyutils as h

####################################################################
# 1. Collect stats for all teams for a given season
####################################################################
def teamstatspull(season,apiurl,outds):
	thisurl=apiurl+'/teams/?expand=team.stats&season='+repr(season)
	r=h.pulldown(thisurl,outds)
	return(r)

####################################################################
# 2. Generic load of json single-season stats data from a 
#    local json file. A file pulled with teamstatspull will work
#    as an input
####################################################################
def statssingleseason(outds,season):
	# open the json file
	with open(outds, 'r') as json_file:
		json_work = json.load(json_file)

	# get the team stats and splits data
	df = pd.io.json.json_normalize(json_work['teams'],['teamStats','splits'],['id'])

	# get the number of rows in the dataframe
	nrows=df.shape[0]

	# select the raw stats, not the rankings
	df2=df.copy(deep=True).iloc[range(0,nrows,2),:]

	# rename id
	df2.rename(index=str, columns={'id': 'teamid'},inplace=True)

	# transfer it into a dataframe with the right structure
	teamstats=pd.DataFrame(df2['stat'].tolist(),index=df2['teamid'].tolist())
	return(teamstats)

####################################################################
# 3. Generic load of json conference, location, and franchise data
# A file pulled with teamstatspull will work as an input
####################################################################
def teammeta(outds):
	with open(outds, 'r') as json_file:
		json_work = json.load(json_file)
	df = pd.io.json.json_normalize(json_work['teams'])
	df.rename(index=str, columns={'id': 'teamid'},inplace=True)
	df.set_index('teamid',inplace=True)
	df.drop(columns=['teamStats'],inplace=True)
	return(df)




####################################################################
# 4. Pull teamstats for an arbitrary list of seasons
####################################################################
def statsmultiseason(outloc,seasons,apiurl,remote=0,handle='allstats'):
	tslist=[]
	tilist=[]
	for season in seasons:
		stem=handle+repr(season)
		outds=outloc+'/'+stem
		outcsv=outloc+'/'+stem+'.csv'
	
		# if remote=1, get data from the NHL API, else local data
		# actually pull the data and save it locally in file outds
		if remote==1:
			teamstatspull(season,apiurl,outds)
	
		# Create a dataset with single-season stats from teamstatspull:
		teamstats=statssingleseason(outds,season)
		tslist.append(teamstats)
	
		# Pull team-level data
		teaminfo=teammeta(outds)
		tilist.append(teaminfo)

	teamstats=pd.concat(tslist,keys=seasons,names=['season','teamid'],sort=True)
	teaminfo=pd.concat(tilist,keys=seasons,names=['season','teamid'],sort=True)

	return([teamstats,teaminfo])



