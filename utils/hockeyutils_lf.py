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
# Load a particular type of play from a giant livefeed file
# using pullplaytype and flatten it
#############################################################

def playdata(r,playtype):

	playlist=pullplaytype(r,playtype)

	if playtype=='SHOT':
		p=json_normalize(playlist)
# Old version:
#		p['shooterdict']=extractplayerv(p['players'],'Shooter')
#		shooter=h.flatten(p,'shooterdict',stem='s.')
#		shooter2=h.flatten(shooter,'s.player',stem='s.')
#		p['goaliedict']=extractplayerv(p['players'],'Goalie')
#		goalie=h.flatten(p,'goaliedict',stem='g.')
#		goalie2=h.flatten(goalie,'g.player',stem='g.')
#		p=p.join([shooter,shooter2,goalie,goalie2])
#		p.drop(columns=['shooterdict','goaliedict','s.player','g.player'],inplace=True)
#		p.set_index('about.eventIdx',inplace=True)
#		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])


		shooter,shooter2=unpackplayer(p,'Shooter','s.')
		goalie,goalie2=unpackplayer(p,'Goalie','g.')
		p=p.join([shooter,shooter2,goalie,goalie2])
		p.drop(columns=['Shooterdict','Goaliedict','s.player','g.player'],inplace=True)
		p.set_index('about.eventIdx',inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])



	if playtype=='BLOCKED_SHOT':
		print('entered BLOCKED_SHOT')
		p=json_normalize(playlist)

		shooter,shooter2=unpackplayer(p,'Shooter','s.')
		blocker,blocker2=unpackplayer(p,'Blocker','b.')
		p=p.join([shooter,shooter2,blocker,blocker2])
		p.drop(columns=['Shooterdict','Blockerdict','s.player','b.player'],inplace=True)

		p.set_index('about.eventIdx',inplace=True)
		p['coordinates.x']=recenterv(p['about.period'],p['about.periodType'],p['coordinates.x'])


	return(p)

