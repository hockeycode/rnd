import pandas as pd
import numpy as np 
from pandas.io.json import json_normalize
import hockeyutils as h

##############################################################
##############################################################
# hockeyutils_base
# very minimal pull-the-data-from-the-api scripts
# contains no data processing except for "no data" null 
# handling
#
# every pull targets a single batch of json; iteration over
# multiple pulls should be handled elsewhere
#
# because this is designed for pulling large amounts of data
# for analysis, when there are both "one" and "multi" options,
# it covers only the "multi" option. For example, there are
# options to pull one team's information or all teams' 
# information. I have only coded the latter.
#
# I have skipped anything about rankings, on-pace, standings,
# prospects, etc. because they are boring, but there may be 
# something helpful for modeling down the road
#
# every script produces:
#	(1) json from pullldown if the location is remote
#	(2) a pandas dataframe (or several) with the basic
#	    output from that file
#	(3) if selected, csv versions of those dataframes
##############################################################
##############################################################


##############################################################
# (1) Standard unpacking script
# specify target information as ['key']['ij']['key'] etc.
##############################################################
def deepdive(constructor,p,ii=0):
	if ii<len(p)-1:
		if p[ii]=='ij':
			newconstructor=[]
			for ik in range(len(constructor)):
				newconstructor.extend(deepdive(constructor[ik],p,ii+1))
			return(newconstructor)
		else:
			return(deepdive(constructor[p[ii]],p,ii+1))
	else:
		if p[ii]=='ij':
			return(constructor)
		else:
			if type(constructor[p[ii]])==list:
				return(constructor[p[ii]])
			else:
	 			return([constructor[p[ii]]])



##############################################################
# (2) Standard unpacking script modified to grab an index 
# from another part of the json
# specify target information as ['key']['ij']['key'] etc.
# specify the index the same way
# when the two paths fork, that's where you grab the index
# and attach it to all the values below the fork point
##############################################################
def getstickyindex(constructor,moreconstructor,indexp,ii):
	stickyindex=[]
	stickyindex=constructor
	for ik in range(ii+1,len(indexp),1):
		if indexp[ik]=='ij':
			print('error at '+repr(ik))
		else:
			stickyindex=stickyindex[indexp[ik]]

	for im in range(len(moreconstructor)):
		if type(moreconstructor[im])==dict:
			moreconstructor[im]['stickyindex']=stickyindex
		else:
			moreconstructor[im]={'values':moreconstructor[im],'stickyindex':stickyindex}
	return(moreconstructor)

def deepdivewithindex(constructor,p,indexp,ii=0,forkpoint=None):
	if forkpoint is None:
		forkpoint=max([(x if (p[x]==indexp[x]) else 0) for x in range(min(len(p),len(indexp)))])

	if ii<len(p)-1:
		if p[ii]=='ij':
			newconstructor=[]
			for ik in range(len(constructor)):
				moreconstructor=deepdivewithindex(constructor[ik],p,indexp,ii+1,forkpoint=forkpoint)
				if ii==forkpoint:
					moreconstructor=getstickyindex(constructor[ik],moreconstructor,indexp,ii)
				newconstructor.extend(moreconstructor)
		else:
			moreconstructor=deepdivewithindex(constructor[p[ii]],p,indexp,ii+1,forkpoint=forkpoint)
			if ii==forkpoint:
				moreconstructor=getstickyindex(constructor,moreconstructor,indexp,ii)
			newconstructor=moreconstructor
		return(newconstructor)

	else:
		if p[ii]=='ij':
			return(constructor)
		else:
			if type(constructor[p[ii]])==list:
				return(constructor[p[ii]])
			else:
	 			return([constructor[p[ii]]])



##############################################################
# (3) demote a dictionary key to an item in a sub-dictionary
#     Note that the API frequently has stuff like this:
#                        "ID8477462": {
#                            "person": {
#                                "shootsCatches": "L", 
#                                "fullName": "Robert Hagg", 
#                                "rosterStatus": "Y", 
#                                "link": "/api/v1/people/8477462", 
#                                "id": 8477462
#                            }, ...etc.
#    It doesn't really make sense to me that you have what is 
#    actually a primary key functioning as a key for the 
#    higher-level dictionary. Probably there's a way to deal
#    with this efficiently -- maybe this is the preferred
#    set-up. It makes my brain hurt, though, so this script
#    will convert a dictionary with keys that are effectively
#    primary keys into a list in which the primary key is
#    a new variable
##############################################################

def demote(d,newname='primarykey'):
	dlist=[]
	for k in d:
		d1=d[k]
		d1[newname]=k
		dlist.append(d1)
	return(dlist)
	

##############################################################
# (4) Construct rename dictionaries to yield shorter, simpler
#     variable names. If all renames run off of this function,
#     it means that I don't need to update lots of places
#     if naming conventions change
##############################################################
def batchrename(currentvars,categories,stem='',oldstem=''):

	renamedict={}

	# franchise attributes
	if 'franchise' in categories:
		renamedict.update({
			'franchise.franchiseId':'franchid',
			'franchise.link':'f.link',
			'franchise.teamName':'f.teamname',
			'franchiseId':'franchid2',
			})

	# Venue attributes
	if 'venue' in categories:
		renamedict.update({
			'venue.city':'v.city',
			'venue.id':'venueid',
			'venue.link':'v.link',
			'venue.name':'v.name',
			'venue.timeZone.id':'v.tz.id',
			'venue.timeZone.offset':'v.tz.offset',
			'venue.timeZone.tz':'v.tz'
			})
	
	# Conference attributes
	if 'conference' in categories:
		renamedict.update({
			'conference.id':'confid',
			'conference.link':'c.link',
			'conference.name':'c.name'
			})

	# Division attributes
	if 'division' in categories:
		renamedict.update({
			'division.abbreviation':'d.abbrev',
			'division.id':'divnid',
			'division.link':'d.link',
			'division.name':'d.name',
			'division.nameShort':'d.nameshort'		
			})

	# Team attributes
	if 'team' in categories:
		renamedict.update({
			'team.id':'teamid',
			'team.link':'t.link',
			'team.name':'t.name',
			'currentTeam.id':'cur.teamid',
			'currentTeam.link':'cur.t.link',
			'currentTeam.name':'cur.t.name',
			'opponent.id':'op.teamid',
			'opponent.link':'op.t.link',
			'opponent.name':'op.t.name'
			})

	# Team attributes, without team. leading string
	if 'team2' in categories:
		renamedict.update({
			'locationName':'t.loc',
			'name':'t.fullname',
			'shortName':'t.shortname',
			'teamName':'t.name',
			'abbreviation':'t.abbrev',
			'link':'t.link',
			'officialSiteUrl':'t.officialsiteurl',
			'firstYearOfPlay':'t.firstyearofplay'
			})

	# Player attributes
	if 'player' in categories:
		renamedict.update({
			'person.fullName':'p.name',
			'person.id':'personid',
			'person.link':'p.link',
			'jerseyNumber':'p.jerseynumber',
			'person.active':'p.active',
			'person.active':'p.active',
			'person.alternateCaptain':'p.alternate',
			'person.birthCity':'p.birthcity',
			'person.birthCountry':'p.birthcountry',
			'person.birthDate':'p.birthdate',
			'person.birthStateProvince':'p.birthstprov',
			'person.captain':'p.captain',
			'person.currentAge':'p.currentage',
			'person.firstName':'p.firstname',
			'person.height':'p.height',
			'person.lastName':'p.lastname',
			'person.nationality':'p.nationality',
			'person.primaryNumber':'p.primarynumber',
			'person.rookie':'p.rookie',
			'person.rosterStatus':'p.roster',
			'person.shootsCatches':'p.shootscatches',
			'person.weight':'p.weight'
	
			})

	# Position attributes
	if 'position' in categories:
		renamedict.update({
			'position.abbreviation':'pos.abbrev',
			'position.code':'pos.code',
			'position.name':'pos.name',
			'position.type':'pos.type',
			'primaryPosition.abbreviation':'prim.pos.abbr',
			'primaryPosition.code':'prim.pos.code',
			'primaryPosition.name':'prim.pos.name',
			'primaryPosition.type':'prim.pos.type',
			})

	# Game attributes
	if 'game' in categories:
		renamedict.update({
			'content.link':'g.contentlink',
			'gameDate':'g.date',
			'gamePk':'gameid',
			'gameType':'g.type',
			'link':'g.link',
			'status.abstractGameState':'g.abstractstate',
			'status.codedGameState':'g.codedstate',
			'status.detailedState':'g.detailedstate',
			'status.startTimeTBD':'g.starttimetbd',
			'status.statusCode':'g.statuscode',
			'game.content.link':'g.contentlink',
			'game.gamePk':'gameid',
			'game.link':'g.link'
			})

	# League record attributes
	if 'leaguerecord' in categories:
		renamedict.update({
			'leagueRecord.losses':'lr.losses',
			'leagueRecord.ot':'lr.otlosses',
			'leagueRecord.type':'lr.type',
			'leagueRecord.wins':'lr.wins'
			})

	# standardized stats attributes
	statsdict={
			# Overall metrics
			'games':'games',
			'goals':'goals',
			'assists':'assists',
			'points':'points',
			'plusMinus':'plusminus',
			'shifts':'shifts',
			'overTimeGoals':'otgoals',
			'gameWinningGoals':'gwgoals',
			'blocked':'blocked',
			'hits':'hits',
			'penaltyMinutes':'pimtxt',
			'pim':'pim',
			'shots':'shots',
			'shotPct':'shotpct',
			'timeOnIce':'toi',
			'timeOnIcePerGame':'toigame',
			'decision':'decision',
			'giveaways':'giveaways',
			'takeaways':'takeaways',

			# Faceoff stats
			'faceOffPct':'faceoffpct',
			'faceOffWinPercentage':'faceoffpct',
			'faceOffWins':'faceoffwins',
			'faceoffTaken':'faceofftaken',


			# Even strength
			'evenTimeOnIce':'eventoi',
			'evenTimeOnIcePerGame':'eventoigame',


			# Power play
			'powerPlayAssists':'ppassists',
			'powerPlayGoals':'ppgoals',
			'powerPlayPoints':'pppoints',
			'powerPlayTimeOnIce':'pptoi',
			'powerPlayTimeOnIcePerGame':'pptoigame',
			'powerPlayOpportunities':'ppopportunities',
			'powerPlayPercentage':'pppctg',


			# Short-handed
			'shortHandedAssists':'shassists',
			'shortHandedGoals':'shgoals',
			'shortHandedPoints':'shpoints',
			'shortHandedTimeOnIce':'shtoi',
			'shortHandedTimeOnIcePerGame':'shtoigame',

			# Goalies
			'evenSaves':'evsaves',
			'evenShotsAgainst':'evsa',
			'evenStrengthSavePercentage':'evsavpctg',
			'powerPlaySavePercentage':'ppsavpctg',
			'powerPlaySaves':'ppsaves',
			'powerPlayShotsAgainst':'ppsa',
			'savePercentage':'savpctg',
			'saves':'saves',
			'shortHandedSaves':'shsaves',
			'shortHandedShotsAgainst':'shsa',
			'shortHandedSavePercentage':'shsavpctg',
			'shots':'shots'
		}
	
	if 'playerstats' in categories:
		renamedict.update(statsdict)

	if 'playerstats2' in categories:
		statsdict2={}
		for k in statsdict:
			statsdict2['stat.'+k]='p.'+statsdict[k]
		renamedict.update(statsdict2)


	# Player goals attributes
	if 'playergoals' in categories:
		renamedict.update({
			'emptyNetGoals':'p.eng',
			'gameWinningGoals':'p.gwgoals',
			'goalsInFirstPeriod':'p.goals1p',
			'goalsInOvertime':'p.otgoals',
			'goalsInSecondPeriod':'p.goals2p',
			'goalsInThirdPeriod':'p.goals3p',
			'goalsLeadingByOne':'p.goalslead1',
			'goalsLeadingByTwo':'p.goalslead2',
			'goalsTrailingByOne':'p.goalslag1',
			'goalsTrailingByTwo':'p.goalslag2',
			'goalsTrailingByThreePlus':'p.goalslag3',
			'goalsWhenTied':'p.goalstied',
			'penaltyGoals':'p.goalspenalty',
			'penaltyShots':'p.shotspenalty',
			'shootOutGoals':'p.goalsso',
			'shootOutShots':'p.shotsso',			
			'stat.emptyNetGoals':'eng',
			'stat.gameWinningGoals':'gwgoals',
			'stat.goalsInFirstPeriod':'goals1p',
			'stat.goalsInOvertime':'otgoals',
			'stat.goalsInSecondPeriod':'goals2p',
			'stat.goalsInThirdPeriod':'goals3p',
			'stat.goalsLeadingByOne':'goalslead1',
			'stat.goalsLeadingByTwo':'goalslead2',
			'stat.goalsTrailingByOne':'goalslag1',
			'stat.goalsTrailingByTwo':'goalslag2',
			'stat.goalsTrailingByThreePlus':'goalslag3',
			'stat.goalsWhenTied':'goalstied',
			'stat.penaltyGoals':'goalspenalty',
			'stat.penaltyShots':'shotspenalty',
			'stat.shootOutGoals':'goalsso',
			'stat.shootOutShots':'shotsso'			

			})

	# select entries and add the stem (if selected)
	if stem is None:
		stem=''
	renamedict={oldstem+k:renamedict[k] for k in renamedict}
	renamedict={k:stem+renamedict[k] for k in renamedict if k in currentvars}
		
	return(renamedict)



##############################################################
# (5) Standardized request to rename things, set the index,
#     and drop unneeded columns. Runs after json normalize
##############################################################
def polish(df,renamecat=None,indexvar=None,morerename=None,dropvars=None,stem=None):

	if renamecat is not None:
		renamedict=batchrename(df.keys(),renamecat,stem=stem)
		df.rename(columns=renamedict,inplace=True)

	if morerename is not None:
		df.rename(columns=morerename,inplace=True)

	if dropvars is not None:
		df.drop(columns=dropvars,inplace=True)

	if indexvar is not None:
		df.set_index(indexvar,inplace=True)
	
	return(df)


##############################################################
# (6) Process team data from a pull like this:
#    https://statsapi.web.nhl.com/api/v1/teams
# every script produces:
#	(1) json from pullldown if the location is remote
#	(2) a pandas dataframe (or several) with the basic
#	    output from that file
#	(3) if selected, csv versions of those dataframes
# Note that there are three options for where you get the 
# data:
#       (1) pulled remotely (in which case inurl and outloc
#           both must be specified)
#       (2) loaded from a local file (requires only outloc)
#       (3) from already-loaded json (requires rawjson)
# Also note that outcsv should not have a '.csv' stem - that
# is added as part of the script
##############################################################
def pullteams(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):
	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	df=json_normalize(r['teams'])

	df=polish(df,
		renamecat=['franchise','venue','conference','division','team2'],
		indexvar=['teamid'],
		morerename={'id':'teamid'},
		dropvars=['franchid2'],
		stem=stem)

	# write to csv if requested
	if outcsv is not None:
		df.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')

	return(df)


##############################################################
# (7) Process team stats (all teams/one season) from this pull:
#     https://statsapi.web.nhl.com/api/v1/teams?expand=team.stats&season=20172018
##############################################################
def pullteamstats(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):
	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	#####################################################
	# pull team metadata
	dfteam=json_normalize(r['teams'])
	
	dfteam=polish(dfteam,
		renamecat=['franchise','venue','conference','division','team2'],
		indexvar=['teamid'],
		morerename={'id':'teamid'},
		dropvars=['teamStats','franchid2'],
		stem=stem)


	#####################################################
	# pull team stats
	r1=deepdivewithindex(r,['teams','ij','teamStats','ij'],['teams','ij','id'],ii=0)

	rn=[{
		#'teamid':rr['stickyindex'],
		'type':rr['type']['displayName'],
		'n':rr['splits'][0]['stat'],
		'team':rr['splits'][0]['team'],
		} 
		for rr in r1]
	rrank=[{
		#'teamid':rr['stickyindex'],
		'type':rr['type']['displayName'],
		'rank':rr['splits'][1]['stat'],
		'team':rr['splits'][1]['team']
		} 
		for rr in r1]

	# convert ranks into integers
	for rr in rrank:
		for k in rr['rank']:
			rr['rank'][k]=int(rr['rank'][k][:-2])

	# switch to dataframe
	dfn=json_normalize(rn)
	dfrank=json_normalize(rrank)

	dfteam=polish(dfn,renamecat=['team'],indexvar=['teamid'],stem=stem)
	dfrank=polish(dfrank,renamecat=['team'],indexvar=['teamid'],stem=stem)

	if outcsv is not None:
		dfteam.to_csv(path_or_buf=outcsv+'_team.csv',encoding='utf-8')
		dfn.to_csv(path_or_buf=outcsv+'_n.csv',encoding='utf-8')
		dfrank.to_csv(path_or_buf=outcsv+'_rank.csv',encoding='utf-8')

	return(dfteam,dfn,dfrank)


##############################################################
# (8) Process team rosters (all teams/one season) from this pull:
#     https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster&season=20172018
##############################################################
def pullrosters(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	#####################################################
	# pull team metadata
	dfteam=json_normalize(r['teams'])

	dfteam=polish(dfteam,
		renamecat=['franchise','venue','conference','division','team2'],
		indexvar=['teamid'],
		morerename={'id':'teamid','roster.link':'r.link'},
		dropvars=['roster.roster','franchid2'],
		stem=stem)

	#####################################################
	# pull roster data
	rlist=deepdivewithindex(r,['teams','ij','roster',u'roster','ij'],['teams','ij','id'],ii=0)
	roster=json_normalize(rlist)
	roster=polish(roster,
		renamecat=['player','position'],
		indexvar=['teamid','personid'],
		morerename={'stickyindex':'teamid'},
		stem=stem)

	if outcsv is not None:
		dfteam.to_csv(path_or_buf=outcsv+'_team.csv',encoding='utf-8')
		roster.to_csv(path_or_buf=outcsv+'_roster.csv',encoding='utf-8')

	return(dfteam,roster)



##############################################################
# (9) Process team schedules (all teams/one daterange) from this pull:
#     https://statsapi.web.nhl.com/api/v1/schedule?startDate=2017-10-10&endDate=2017-10-16',
##############################################################

def pullschedule(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])


	#####################################################
	# pull query metadata, level 0
	dfmeta0=json_normalize(r)
	dfmeta0.drop(columns=['dates','copyright'],inplace=True)

	#####################################################
	# pull query metadata, level 1
	dfmeta1=json_normalize(r['dates'])
	dfmeta1.drop(columns=['games','events','matches'],inplace=True)

	#####################################################
	# pull game data
	rr=deepdivewithindex(r,['dates','ij','games'],['dates','ij','date'],ii=0)
	dfgames=json_normalize(rr)

	# more extensive renaming due to the depth of the json
	modnames={'stickyindex':'date','teams.home.score':'h.score','teams.away.score':'a.score'}
	modnames.update(batchrename(dfgames.keys(),['team','leaguerecord'],stem='h.',oldstem='teams.home.'))
	modnames.update(batchrename(dfgames.keys(),['team','leaguerecord'],stem='a.',oldstem='teams.away.'))

	dfgames=polish(dfgames,
		renamecat=['venue','game'],
		indexvar=['gameid'],
		morerename=modnames,
		stem=stem)

	if outcsv is not None:
		dfmeta0.to_csv(path_or_buf=outcsv+'_meta0.csv',encoding='utf-8')
		dfmeta1.to_csv(path_or_buf=outcsv+'_meta1.csv',encoding='utf-8')
		dfgames.to_csv(path_or_buf=outcsv+'_games.csv',encoding='utf-8')

	return(dfmeta0,dfmeta1,dfgames)	


##############################################################
# (10) Pull single-player snapshot (no stats) from this pull:
#     https://statsapi.web.nhl.com/api/v1/people/8473563
##############################################################
def pullplayer(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	dfplayer=json_normalize(r['people'])

	dfplayer=polish(dfplayer,
		renamecat=['team','position'],
		indexvar=['personid'],
		morerename={'id':'personid'},
		stem=stem)

	if outcsv is not None:
		dfplayer.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')
	
	return(dfplayer)


##############################################################
# (11) Pull single-player, single-season stats from this pull:
#     https://statsapi.web.nhl.com/api/v1/people/8473563/stats?stats=statsSingleSeason&season=20172018
##############################################################

def pullplayerstats(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	dfstats=json_normalize(r['stats'][0]['splits'])

	modnames={}
	modnames.update(batchrename(dfstats.keys(),['playerstats'],stem='p.',oldstem='stat.'))

	dfstats=polish(dfstats,
		indexvar=['season'],
		morerename=modnames,
		stem=stem)

	if outcsv is not None:
		dfstats.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')

	return(dfstats)


##############################################################
# (12) Pull single-player, single-season game logs from this 
#     pull:
#     https://statsapi.web.nhl.com/api/v1/people/8473563/stats?stats=gameLog&season=20172018',
#     Note that there are all sorts of custom metrics (e.g.
#     home and away pulls) but everything like that can just
#     be calculated from the gamelog data
##############################################################

def pullplayergl(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])
	
	dfgamelog=json_normalize(r['stats'][0]['splits'])

	modnames={}
	modnames.update(batchrename(dfgamelog.keys(),['playerstats'],stem='p.',oldstem='stat.'))

	dfgamelog=polish(dfgamelog,
		renamecat=['team','game'],
		indexvar=['gameid'],
		morerename=modnames,
		stem=stem)

	if outcsv is not None:
		dfgamelog.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')

	return(dfgamelog)


##############################################################
# (13) Pull single-player, single-season goals by game
#     situation from this pull:
#     https://statsapi.web.nhl.com/api/v1/people/8473563/stats?stats=goalsByGameSituation&season=20172018
#     Note that this can be calculated from the linescore data
#     but that would be kind of labor-intensive for stupid
#     stats like this. Why am I even coding this?
##############################################################

def pullplayergoals(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	dfgoals=json_normalize(r['stats'][0]['splits'][0])

	dfgoals=polish(dfgoals,
		renamecat=['playergoals'],
		indexvar=['season'],
		stem=stem)

	if outcsv is not None:
		dfgoals.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')

	return(dfgoals)


##############################################################
# (14) Pull boxscore data from this pull:
#     https://statsapi.web.nhl.com/api/v1/game/2017020066/boxscore
##############################################################

def pullboxscore(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])

	#####################################################
	# Pull officials data
	dfoff=json_normalize(r['officials'])

	#####################################################
	# Pull player data
	hp=demote(r['teams']['home']['players'],newname='personidtxt')
	ap=demote(r['teams']['away']['players'],newname='personidtxt')
	hp.extend(ap)
	dfplayers=json_normalize(hp)

	# deal with variables that are duplicated between players
	# and goalies
	dfplayers['p.assists']=dfplayers['stats.skaterStats.assists'].combine_first(dfplayers['stats.goalieStats.assists'])
	dfplayers['p.goals']=dfplayers['stats.skaterStats.goals'].combine_first(dfplayers['stats.goalieStats.goals'])
	dfplayers['p.shots']=dfplayers['stats.skaterStats.shots'].combine_first(dfplayers['stats.goalieStats.shots'])
	dfplayers['p.pim']=dfplayers['stats.skaterStats.penaltyMinutes'].combine_first(dfplayers['stats.goalieStats.pim'])
	dfplayers['p.toi']=dfplayers['stats.skaterStats.timeOnIce'].combine_first(dfplayers['stats.goalieStats.timeOnIce'])
	dfplayers.drop(columns=['stats.skaterStats.assists',
				'stats.skaterStats.penaltyMinutes',
				'stats.skaterStats.timeOnIce',
				'stats.skaterStats.shots',
				'stats.skaterStats.goals',
				'stats.goalieStats.assists',
				'stats.goalieStats.pim',
				'stats.goalieStats.timeOnIce',
				'stats.goalieStats.shots',
				'stats.goalieStats.goals'],inplace=True)



	# person.primaryPosition,person.currentTeam, position, player stats
	modnames={}
	modnames.update(batchrename(dfplayers.keys(),['team','position'],stem='',oldstem='person.'))
	modnames.update(batchrename(dfplayers.keys(),['playerstats'],stem='p.',oldstem='stats.skaterStats.'))
	modnames.update(batchrename(dfplayers.keys(),['playerstats'],stem='p.',oldstem='stats.goalieStats.'))

	# polish player data
	dfplayers=polish(dfplayers,
		renamecat=['player','position'],
		indexvar=['personid'],
		morerename=modnames,
		stem=stem)

	#####################################################
	# Pull team data
	rt=[r['teams']['home']]
	rt.append(r['teams']['away'])
	dfteams=json_normalize(rt)

	# playerstats for the game
	modnames=batchrename(dfteams.keys(),['playerstats'],stem='t.',oldstem='teamStats.teamSkaterStats.')

	# attributes to drop
	dropnames=[x for x in dfteams.columns if x[0:7]=='players']
	dropnames.extend(['coaches','goalies','onIce','onIcePlus','penaltyBox','scratches','skaters'])

	# polish player data
	dfteams=polish(dfteams,
		renamecat=['team'],
		indexvar=['teamid'],
		morerename=modnames,
		dropvars=dropnames,
		stem=stem)

	#####################################################
	# Pull coaches
	coaches=[]
	coaches=r['teams']['home']['coaches']
	coaches.extend(r['teams']['away']['coaches'])
	dfcoaches=json_normalize(coaches)

	# polish player data
	dfcoaches=polish(dfcoaches,
		renamecat=['player','position'],
		stem=stem)

	#####################################################
	# Pull player index -- just playerid, team, and role
	# for role in [skater,goalie,scratch]
	playerindex=[]
	for team in ['home','away']:
		teamid=r['teams'][team]['team']['id']
		for playertype in ['goalies','skaters','scratches']:
			for p in r['teams'][team][playertype]:
				for x in r['teams'][team][playertype]:
					xval={'personid':x,'playertype':playertype,'teamid':teamid}
					playerindex.append(xval)
	
	dfplindex=json_normalize(playerindex)
	dfplindex.set_index(['personid'],inplace=True)

	#####################################################
	# write data to csv if requested
	if outcsv is not None:
		dfoff.to_csv(path_or_buf=outcsv+'_officials.csv',encoding='utf-8')
		dfplayers.to_csv(path_or_buf=outcsv+'_players.csv',encoding='utf-8')
		dfteams.to_csv(path_or_buf=outcsv+'_teams.csv',encoding='utf-8')
		dfcoaches.to_csv(path_or_buf=outcsv+'_coaches.csv',encoding='utf-8')
		dfplindex.to_csv(path_or_buf=outcsv+'_plindex.csv',encoding='utf-8')

	

	return(dfoff,dfplayers,dfteams,dfcoaches,dfplindex)


##############################################################
# (15) Pull livefeed data from this pull:
#     https://statsapi.web.nhl.com/api/v1/game/2017020066/feed/live
##############################################################
def pulllivefeed(rawjson=None,inurl='',outloc='',outcsv=None,stem=''):

	if rawjson is None:
		r=h.pulldown(inurl=inurl,outfile=outfile)
	else:
		r=rawjson

	if 'copyright' in r:
		print(r['copyright'])


	dfoff,dfplayers,dfteams,dfcoaches,dfplindex=pullboxscore(rawjson=r['liveData']['boxscore'],outcsv=outcsv)
	return(dfoff,dfplayers,dfteams,dfcoaches,dfplindex)



	














	
##############################################################
# (Z) take a list of stat dictionaries (e.g. [home,away]) and
#     pivot it 
#     data structure assumes:
#     outerlist=[
#		[{'category':'a',
#		'stats':{....}},
#		{'category':'b',
#		'stats':{....}}],
#		[{'category':'a',
#		'stats':{....}},
#		{'category':'b',
#		'stats':{....}}]
#		]
##############################################################
#def pivotlist(outerlist,metrickeys,cat,stemdict,primarykeylist=None):
#	transposed=[]
#	for ii in range(len(outerlist)):
#		onerow={stemdict[y[cat]]+m:y[m] for y in outerlist[ii] for m in metrickeys}
#		if primarykeylist is not None:
#			print('is not none')
#			onerow['primarykey']=primarykeylist[ii]
#		transposed.append(onerow)
#	return(transposed)




