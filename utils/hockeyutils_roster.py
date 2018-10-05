# Roster information from the NHL API
# 1. Collect rosters for all teams for a given season
# 2. Generic load of json single-season roster data from a 
#    local json file.
# 3. Pull teamrosters for an arbitrary list of seasons

# Notes:
# - this is compatible with the new version of pulldown in hockeyutils2,
#   but it doesn't fully take advantage of that structure. Need to
#   recode this section if I decide I like that wrapper


import pandas as pd
import numpy as np 
import json
import hockeyutils2 as h


####################################################################
# 1. Collect rosters for all teams for a given season
####################################################################
def teamrosterpull(season,apiurl,outds):
	thisurl=apiurl+'/teams/?expand=team.roster&season='+repr(season)
	r=h.pulldown(thisurl,outds)
	return(r)


####################################################################
# 2. Generic load of json single-season roster data from a 
#    local json file. A file pulled with teamrosterpull will work
#    as an input
####################################################################
def rostersingleseason(outds,season):
	with open(outds, 'r') as json_file:
		json_roster = json.load(json_file)

	# read in the data and set the index teamid x personid
	df=pd.io.json.json_normalize(json_roster['teams'],[['roster','roster']],['id'])
	df=h.indextract(df,['person','id'])
	df.rename(columns={'id': 'teamid'},inplace=True)
	df.rename(columns={'person.id': 'personid'},inplace=True)
	df['personid']=df['personid'].fillna(0).astype(int)
	df.set_index(['teamid','personid'],inplace=True,verify_integrity=True)

	# clean up jerseyNumber because it comes through as an object
	# some people don't have jersey numbers, so set those to -1
	df[['jerseyNumber']] = df[['jerseyNumber']].apply(pd.to_numeric, errors='coerce')
	df['jerseyNumber']=df['jerseyNumber'].fillna(-1).astype(int)

	# flatten position and person -- columns of dictionaries
	persondf=h.flatten(df,'person',skip=['id'])
	positiondf=h.flatten(df,'position',stem='pos.')

	# remove person and position, since they have been unpacked
	df.drop(columns=['person','position'],inplace=True)

	# put all the data back together
	df=df.join([persondf,positiondf], how='outer')

	return(df)

####################################################################
# 3. Pull teamrosters for an arbitrary list of seasons
####################################################################
def rostersmultiseason(outloc,seasons,apiurl,remote=0,handle='allrosters'):
	trlist=[]
	for season in seasons:
		stem=handle+repr(season)
		outds=outloc+'/'+stem
		outcsv=outloc+'/'+stem+'.csv'
	
		# if remote=1, get data from the NHL API, else local data
		# actually pull the data and save it locally in file outds
		if remote==1:
			teamrosterpull(season,apiurl,outds)
	
		# Create a dataset with team rosters from teamrosterpull:
		teamroster=rostersingleseason(outds,season)
		trlist.append(teamroster)

	teamroster=pd.concat(trlist,keys=seasons,names=['season','teamid','personid'],sort=True)

	return(teamroster)




