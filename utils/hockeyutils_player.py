##########################################################
# Player data
# There are several different sources of player data
# The high-level: https://statsapi.web.nhl.com/api/v1/people/ID
#     but note that that doesn't seem to allow iteration by
#     season
# Stats: https://statsapi.web.nhl.com/api/v1/people/ID/stats
#     This allows lots of individual queries, and iteration
#     by season
#
# Other notes:
# Because of the structure of the data, I'm not building a local
# option to read in the data for now. May need to create one
# for unit testing ease
# There are lots of other forms of stratification, e.g. 
# by month, but they can all be derived from playergamelog
# output
# Sources for tester data for other forms of stratification:
#	thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=byMonth&season='+repr(season)
#	r=h.pulldown(inurl=thisurl,outfile=outloc+'/testMon'+repr(personid))
#	thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=byDayOfWeek&season='+repr(season)
#	r=h.pulldown(inurl=thisurl,outfile=outloc+'/testDay'+repr(personid))
#	thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=vsDivision&season='+repr(season)
#	r=h.pulldown(inurl=thisurl,outfile=outloc+'/testDiv'+repr(personid))
#	thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=vsConference&season='+repr(season)
#	r=h.pulldown(inurl=thisurl,outfile=outloc+'/testConf'+repr(personid))
#	thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=vsTeam&season='+repr(season)
#	r=h.pulldown(inurl=thisurl,outfile=outloc+'/testTeam'+repr(personid))
##########################################################
import pandas as pd
import numpy as np 
import json
import hockeyutils as h
import time

##########################################################
# 1. Playerdata function, which returns data with one row
# for every player for every season; new columns are 
# added for places where there is more than one record per
# player per season, e.g. home vs. away records
##########################################################
def playerdata(outloc,apiurl,sptuples=[],seasons=[],peopleids=[],reporttype=['a'],handle='playerdata',inc=50):

	# tracking, since this can be a long-running program
	counter=0
	tick=time.time()

	# this iterates through tuples. If tuples don't 
	# already exist in sptuples, create sptuples from
	# seasons and peopleids
	if sptuples == []:
		for season in seasons:
			for personid in peopleids:
				sptuples.append((season,personid))

	# iterate through the season x personid tuples to
	# pull data
	indextuples=[]
	dictlist=[]
	for (season,personid) in sptuples:

		# for a given person and season, all the different
		# queries are combined into one dictionary
		combined={}

		# first, a pointer whether there is any data
		dataexist=True
		
		# generic statsSingleSeason gets triggered as 'a'
		if 'a' in reporttype:
			thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=statsSingleSeason&season='+repr(season)
			r=h.pulldown(inurl=thisurl)
			if r['stats'][0]['splits'] == []:
				dataexist=False
			else:
				combined.update(r['stats'][0]['splits'][0]['stat'])
		
		# home-and-away-level data gets triggered as 'ha'
		if 'ha' in reporttype:
			thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=homeAndAway&season='+repr(season)
			r=h.pulldown(inurl=thisurl)

			splits=r['stats'][0]['splits']

			for s in splits:
				if s['isHome']==True:
					modifier='h.'
				else:
					modifier='a.'
				for metric in s['stat']:
					combined[modifier+metric]=s['stat'][metric]	

		# win/loss/overtime loss-level data gets triggered as 'wl'
		if 'wl' in reporttype:
			thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=winLoss&season='+repr(season)
			r=h.pulldown(inurl=thisurl)

			splits=r['stats'][0]['splits']

			for s in splits:
				if s['isOT']==False and s['isWin']==True:
					modifier='w.'
				elif s['isOT']==False and s['isWin']==False:
					modifier='l.'
				elif s['isOT']==True and s['isWin']==False:
					modifier='ot.'
				for metric in s['stat']:
					combined[modifier+metric]=s['stat'][metric]


		# add the record
		if len(combined)>0:
			indextuples.append((season,personid))
			dictlist.append(combined)
		
		# tracking
		counter=counter+1
		tock=time.time()
		if counter%inc==0:
			print('Reached '+repr(counter)+' after '+repr(tock-tick)+' seconds')

	playerindex=pd.MultiIndex.from_tuples(indextuples,names=['season','personid'])
	df=pd.DataFrame(dictlist,index=playerindex,copy=True)
		

	return(df)

##########################################################
# 2. playergamelog function
##########################################################
def playergamelog(outloc,apiurl,sptuples=[],seasons=[],peopleids=[]):

	# this iterates through tuples. If tuples don't 
	# already exist in sptuples, create sptuples from
	# seasons and peopleids
	if sptuples == []:
		for season in seasons:
			for personid in peopleids:
				sptuples.append((season,personid))

	# iterate through the season x personid tuples to
	# pull data
	indextuples=[]
	pgllist=[]
	for (season,personid) in sptuples:

		thisurl=apiurl+'/people/'+repr(personid)+'/stats?stats=gameLog&season='+repr(season)
		r=h.pulldown(inurl=thisurl)
		if r['stats'][0]['splits'] != []:
			df = pd.io.json.json_normalize(r['stats'][0]['splits'])
			df.rename(index=str, columns={'game.gamePk': 'gameid'},inplace=True)
			df.set_index('gameid',inplace=True)

			indextuples.append((season,personid))
			pgllist.append(df)
	
	print(indextuples)
	pgls=pd.concat(pgllist,keys=indextuples,names=['season','personid','gameid'],sort=True)


	return(pgls)


