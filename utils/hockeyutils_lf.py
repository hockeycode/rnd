#############################################################
# Assorted tools to read livefeed data
#############################################################
import requests
import pandas as pd
from pandas.io.json import json_normalize
import numpy as np 
import json
import codecs
import hockeyutils as h


#############################################################
# Load a particular type of play from a giant livefeed file
#############################################################
def pullplaytype(r,playtype):
	# this iterates through the play-level data in the
	# json file here:
	#     [u'liveData'][u'plays'][u'allPlays']
	# r is the json file already imported
	# playtype is the type of play

	playlist=[]
	for play in r[u'liveData'][u'plays'][u'allPlays']:
		if play[u'result'][u'eventTypeId']==playtype:
			playlist.append(play)

	return(playlist)


#############################################################
# Flip coordinates for the second period
#############################################################
def recenter(period,periodType,x):
	# in regulation, flip x axis in the second period
	if periodType=='REGULAR':
		if period==2:
			x=-x
		else:
			x=x
	# in overtime, flip x axis in the odd periods
	else: 
		if period%2==1:
			x=-x
		else:
			x=x
	return(x)
recenterv=np.vectorize(recenter)


#############################################################
# Extract players from plays based on player type
#############################################################
def extractplayer(players,playertype):
	for pl in players:
		if pl['playerType']==playertype:
			return(pl)
	return(0)
extractplayerv=np.vectorize(extractplayer)

#############################################################
# Unpack standardized player data
#############################################################
def unpackplayer(p,role,stem):
	p[role+'dict']=extractplayerv(p['players'],role)
	df1=h.flatten(p,role+'dict',stem=stem)
	df2=h.flatten(df1,stem+'player',stem=stem)
	return(df1,df2)

#############################################################
# Dummy data for a player missing information
#############################################################
def dummydata(playertype):
	d={}
	d1={'fullName':None,'link':None,'id':None}
	d['player']=d1
	d['seasonTotal']=None
	d['playerType']=playertype
	return(d)

#############################################################
# Pad assists
#############################################################
def padassists(players):
	playersf=[]
	nassists=0
	for player in players:
		if player['playerType']=='Assist':
			if nassists==0:
				player['playerType']='Assist1'
			elif nassists==1:
				player['playerType']='Assist2'
			nassists=nassists+1
		playersf.append(player)
	if nassists==1:
		playersf.append(dummydata('Assist2'))
	if nassists==0:
		playersf.append(dummydata('Assist1'))
		playersf.append(dummydata('Assist2'))
	return(playersf)
padassistsv=np.vectorize(padassists)

#############################################################
# Pad goalies -- for empty net situations
#############################################################
def padgoalie(players):
	playersf=[]
	ngoalies=0
	for player in players:
		if player['playerType']=='Goalie':
			ngoalie=1
		playersf.append(player)
	if ngoalie==0:
		playersf.append(dummydata('Goalie'))
	return(playersf)
padgoaliev=np.vectorize(padgoalie)

#############################################################
# Pad drawn-by players
#############################################################
def paddrewby(players):
	playersf=[]
	ndrewby=0
	for player in players:
		if player['playerType']=='DrewBy':
			ndrewby=1
		playersf.append(player)
	if ndrewby==0:
		playersf.append(dummydata('DrewBy'))
	return(playersf)
paddrewbyv=np.vectorize(paddrewby)


#############################################################
# Load a particular type of play from a giant livefeed file
# using pullplaytype and flatten it
# Included: u'SHOT', u'HIT',u'GOAL', u'BLOCKED_SHOT',  u'MISSED_SHOT',
# u'FACEOFF', u'GIVEAWAY',u'TAKEAWAY',u'PENALTY',  u'STOP',
# Not included: [u'GAME_END', u'PERIOD_OFFICIAL', u'PERIOD_READY', 
#	u'PERIOD_END', u'PERIOD_START', u'GAME_SCHEDULED',]
#############################################################

def playdata(r,playtype):

	playlist=pullplaytype(r,playtype)
	p=json_normalize(playlist)
	p.set_index('about.eventIdx',inplace=True)

	if playtype=='SHOT':
		p['players']=padgoaliev(p['players'])
		shooter,shooter2=unpackplayer(p,'Shooter','s.')
		goalie,goalie2=unpackplayer(p,'Goalie','g.')
		p=p.join([shooter,shooter2,goalie,goalie2])
		p.drop(columns=['Shooterdict','Goaliedict','s.player','g.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='BLOCKED_SHOT':
		shooter,shooter2=unpackplayer(p,'Shooter','s.')
		blocker,blocker2=unpackplayer(p,'Blocker','b.')
		p=p.join([shooter,shooter2,blocker,blocker2])
		p.drop(columns=['Shooterdict','Blockerdict','s.player','b.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='MISSED_SHOT':
		shooter,shooter2=unpackplayer(p,'Shooter','s.')
		p=p.join([shooter,shooter2])
		p.drop(columns=['Shooterdict','s.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='GOAL':
		p['players']=padgoaliev(p['players'])
		p['players']=padassistsv(p['players'])
		shooter,shooter2=unpackplayer(p,'Scorer','s.')
		goalie,goalie2=unpackplayer(p,'Goalie','g.')
		assist11,assist12=unpackplayer(p,'Assist1','a1.')
		assist21,assist22=unpackplayer(p,'Assist2','a2.')

		p=p.join([shooter,shooter2,goalie,goalie2,assist11,assist12,assist21,assist22])
		p.drop(columns=['Scorerdict','Goaliedict','s.player','g.player',
			'Assist1dict','Assist2dict','a1.player','a2.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='HIT':
		hitter,hitter2=unpackplayer(p,'Hitter','h1.')
		hittee,hittee2=unpackplayer(p,'Hittee','h2.')
		p=p.join([hitter,hitter2,hittee,hittee2])
		p.drop(columns=['Hitterdict','Hitteedict','h1.player','h2.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])
		
	if playtype=='FACEOFF':
		winner,winner2=unpackplayer(p,'Winner','fw.')
		loser,loser2=unpackplayer(p,'Loser','fl.')
		p=p.join([winner,winner2,loser,loser2])
		p.drop(columns=['Winnerdict','Loserdict','fw.player','fl.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype in ['GIVEAWAY','TAKEAWAY']:
		skater,skater2=unpackplayer(p,'PlayerID','s.')
		p=p.join([skater,skater2])
		p.drop(columns=['PlayerIDdict','s.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='PENALTY':
		p['players']=paddrewbyv(p['players'])
		penaltyon,penaltyon2=unpackplayer(p,'PenaltyOn','po.')
		drewby,drewby2=unpackplayer(p,'DrewBy','db.')
		p=p.join([penaltyon,penaltyon2,drewby,drewby2])
		p.drop(columns=['PenaltyOndict','DrewBydict','po.player','db.player'],inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])

	if playtype=='STOP':
		pass


	return(p)


#############################################################
# Load lots of play types into a single dataframe
#############################################################

def multiplays(r,playtypelist):

	r1=[]

	for thisplaytype in playtypelist:
		r1.append(playdata(r,thisplaytype))

	r2=pd.concat(r1,sort=True)

	return(r2)
