import pandas as pd
from pandas.io.json import json_normalize
import numpy as np 
import json
import codecs
import hockeyutils as h

####################################################################
# 1. Fill dataframes with player stats from a single game
#    This is the version compatible with (2) below
####################################################################
def fillstats(r):
	# home
	r1=r['teams']['home']['players']
	r2=[]
	for p in r1:
		tempdict=r1[p]
		tempdict['personid']=int(p[2:])
		r2.append(tempdict)
	home = pd.io.json.json_normalize(r2)
	home.set_index('personid',inplace=True)
	hometeam=r['teams']['home']['team']['id']

	# away
	r1=r['teams']['away']['players']
	r2=[]
	for p in r1:
		tempdict=r1[p]
		tempdict['personid']=int(p[2:])
		r2.append(tempdict)
	away = pd.io.json.json_normalize(r2)
	away.set_index('personid',inplace=True)
	awayteam=r['teams']['away']['team']['id']

	dflist=[home,away]
	teamlist=[hometeam,awayteam]
	combined=pd.concat(dflist,keys=teamlist,names=['teamid','personid'],sort=True)

	return(combined)

####################################################################
# 2. Fill a dataframe with all stats for all games for all players
#    within a season
#    this is incredibly inefficient -- one connection to the NHL api
#    per game -- and will need to be recoded at some point
#    Counterpoint: DATA!
#    Because of the inefficiency (but not mitigating it), this has
#    an interim export-to-csv step 
#    It does not store the raw json files, which maybe it ought
####################################################################

def multiplayergamestats(apiurl,outloc,season):
	gameid=int(repr(season)[0:4]+'020001')
	games=[]
	gamestatlist=[]
	success=1
	while success==1:
		if gameid%20==0:
			print('reached '+repr(gameid))
		if gameid%100==0:
			tock=gameid%10000
			tick=tock-100
			print(tick,tock)
			gamestats=pd.concat(gamestatlist[tick:(tock+1)],keys=games[tick:(tock+1)],names=['gameid','teamid','personid'],sort=True)
			gamestats[gamestats['person.primaryPosition.code']=='G'].to_csv(path_or_buf=outloc+'/goalie'+repr(gameid)+'.csv',encoding='utf-8')
			gamestats[gamestats['person.primaryPosition.code']!='G'].to_csv(path_or_buf=outloc+'/skater'+repr(gameid)+'.csv',encoding='utf-8')
			print('successful export at '+repr(gameid))
	
		thisurl=apiurl+'/game/'+repr(gameid)+'/boxscore'
		r=h.pulldown(inurl=thisurl)
		if 'message' in r:
			success=0
			break
		else:
			c=fillstats(r)
			gamestatlist.append(c)
			games.append(gameid)
			gameid=gameid+1

	print('exited loop at '+repr(gameid))
	
	# cleanup
	gamestats=pd.concat(gamestatlist[tock+1:],keys=games[tock+1:],names=['gameid','teamid','personid'],sort=True)
	gamestats[gamestats['person.primaryPosition.code']=='G'].to_csv(path_or_buf=outloc+'/goalie'+repr(season)+'.csv',encoding='utf-8')
	gamestats[gamestats['person.primaryPosition.code']!='G'].to_csv(path_or_buf=outloc+'/skater'+repr(season)+'.csv',encoding='utf-8')
	
	# overall datasets
	gamestats=pd.concat(gamestatlist,keys=games,names=['gameid','teamid','personid'],sort=True)
	gamestats[gamestats['person.primaryPosition.code']=='G'].to_csv(path_or_buf=outloc+'/goalie'+repr(season)+'.csv',encoding='utf-8')
	gamestats[gamestats['person.primaryPosition.code']!='G'].to_csv(path_or_buf=outloc+'/skater'+repr(season)+'.csv',encoding='utf-8')

	return(gamestats)


####################################################################
# 3. Similar to (2), but if there is a known list of game stats
#    doesn't save to csv or anything, so it is probably best for
#    smaller lists of games
#    Probably should recode to make (2) and (3) more aligned
####################################################################

def multiplayergamestats2(apiurl,outloc,games):
	gamestatlist=[]
	for gameid in games:
		outds=outloc+'/boxscore'+repr(gameid)
		r=h.pulldown(outfile=outds)
		c=fillstats(r)
		gamestatlist.append(c)
	gamestats=pd.concat(gamestatlist,keys=games,names=['gameid','teamid','personid'],sort=True)

	return(gamestats)

####################################################################
# Old. Fill dataframes with player stats from a single game
#    I like the version above better
####################################################################
#def fillstats(r0):
#	# get the list of skaters
#	skaters=r0['skaters']
#	goalies=r0['goalies']
#
#	# available metrics vary from year to year, I think, so look
#	# up what is available this year, checking across all skaters
#	# and goalies, since it even varies player to player
#	skatermetrics=set()
#	goaliemetrics=set()
#	for s in skaters:
#		if 'skaterStats' in r0['players']['ID'+repr(s)]['stats']:
#			skatermetrics.update(r0['players']['ID'+repr(s)]['stats']['skaterStats'])
#	for g in goalies:
#		if 'goalieStats' in r0['players']['ID'+repr(g)]['stats']:
#			goaliemetrics.update(r0['players']['ID'+repr(g)]['stats']['goalieStats'])
#	skatermetrics=list(skatermetrics)
#	goaliemetrics=list(goaliemetrics)
#
#	# initialize the dataframes
#	skaterdf=pd.DataFrame(index=skaters,columns=skatermetrics)
#	goaliedf=pd.DataFrame(index=goalies,columns=goaliemetrics)
#	skaterdf.index.names = ['personid']
#	goaliedf.index.names = ['personid']
#
#	# fill the dataframes
#	r1=r0['players']
#	for personid in skaters:
#		if r1['ID'+repr(personid)]['stats'] != {}:
#			for m in skatermetrics:
#				if m in r1['ID'+repr(personid)]['stats']['skaterStats']:
#					skaterdf.loc[personid,m]=r1['ID'+repr(personid)]['stats']['skaterStats'][m]
#	for personid in goalies:
#		if r1['ID'+repr(personid)]['stats'] != {}:
#			for m in goaliemetrics:
#				if m in r1['ID'+repr(personid)]['stats']['goalieStats']:
#					goaliedf.loc[personid,m]=r1['ID'+repr(personid)]['stats']['goalieStats'][m]
#
#	return(skaterdf,goaliedf)


