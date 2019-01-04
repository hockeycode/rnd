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
import hockeyutils_lf as hlf


#############################################################
# Load the list of names on ice at a given time
#############################################################
def whosonice(p,period,periodtime,eqtype='L'):
	periodtimemin=h.stringtominutes(periodtime)

	selectme=(p['period']==period)

	# constrain to be up to the left endpoint (starttimemin)
	# including the left endpoint iff eqtype in ['L','B']
	if eqtype in ['L','B']:
		selectme=np.logical_and(selectme,p['starttimemin']<=periodtimemin)
	elif eqtype in ['R','N']:
		selectme=np.logical_and(selectme,p['starttimemin']<periodtimemin-.00000001)

	# constrain to be up to the right endpoint (endtimemin)
	# including the right endpoint iff eqtype in ['R','B']
	if eqtype in ['R','B']:
		selectme=np.logical_and(selectme,p['endtimemin']>=periodtimemin)
	elif eqtype in ['L','N']:
		selectme=np.logical_and(selectme,p['endtimemin']>periodtimemin+.00000001)

	shiftlist=p.loc[selectme]
	#shiftlist.set_index('playerId',inplace=True)

	return(shiftlist[['firstName','lastName','teamAbbrev','teamId','typeCode','eventNumber']])


#############################################################
# Event-for indicator (e.g. for calculating plus/minus or
# for calculating goals for per 60)
#############################################################
def calceventforind(livefeed,shifts,playtype):
	# determine which endpoints to include - not fully validated yet
	if playtype in ['GOAL','SHOT','BLOCKED_SHOT','MISSED_SHOT','HIT','GIVEAWAY','TAKEAWAY','PENALTY']:
		eqtype='R'
	elif playtype=='FACEOFF':
		eqtype='L'

	# select all plays with that event, and who was on ice
	evtlist=livefeed[['about.period','about.periodTime']]
	allevents=[]
	allwho=[]
	for ii in range(len(evtlist)):
		allwho.append(whosonice(shifts,
			evtlist.iloc[ii]['about.period'],
			evtlist.iloc[ii]['about.periodTime'],
			eqtype=eqtype))
		allevents.append(evtlist.index[ii])
	oniceevent=pd.concat(allwho,keys=allevents,names=['about.eventIdx'],sort=True)
	renamedict={}
	for v in oniceevent.columns:
		renamedict[v]='onice.'+v
	oniceevent.rename(columns=renamedict,inplace=True)

	# merge in the livefeed data about the event
	oniceevent=oniceevent.join(livefeed, how='outer')

	# set the criterion for for/against
	if playtype in ['GOAL','FACEOFF','SHOT','MISSED_SHOT','HIT','GIVEAWAY','TAKEAWAY','PENALTY']:
		eventforind=(oniceevent['onice.teamId']==oniceevent['team.id'])
	# note that blocked shot have the team = blocker's team, so if
	# we want to align with other shot types, pick !=team.id
	elif playtype=='BLOCKED_SHOT':
		eventforind=(oniceevent['onice.teamId']!=oniceevent['team.id'])
	else:
		eventforind=(oniceevent['onice.teamId']==oniceevent['team.id'])

	# return the merged data and the criterion for/against
	return(oniceevent,eventforind)



#############################################################
# Plus/minus
#############################################################
def calcplusminus(livefeed0,shifts0,playtype='GOAL'):

	# process livefeed json data
	livefeed=hlf.playdata(livefeed0,playtype)

	# process shifts json data
	shifts=json_normalize(shifts0['data'])
	shifts['endtimemin']=h.stringtominutesv(shifts['endTime'])
	shifts['durationmin']=h.stringtominutesv(shifts['duration'])
	shifts['starttimemin']=h.stringtominutesv(shifts['startTime'])
	shifts.set_index('playerId',inplace=True)

	# calculate the "event for" indicator
	oniceevent,eventforind=calceventforind(livefeed,shifts,playtype)

	# calculate plus/minus
	oniceevent['plusminus1']=np.where(eventforind,1,-1)
	plusminus=oniceevent[['plusminus1']].groupby(level=['playerId']).sum()
	#print(plusminus)

	return(plusminus)



#############################################################
# event for/against per 60
#############################################################
def foragainst60(livefeed0,shifts0,playtype='GOAL'):

	# process livefeed json data
	livefeed=hlf.playdata(livefeed0,playtype)

	# process shifts json data
	shifts=json_normalize(shifts0['data'])
	shifts['endtimemin']=h.stringtominutesv(shifts['endTime'])
	shifts['durationmin']=h.stringtominutesv(shifts['duration'])
	shifts['starttimemin']=h.stringtominutesv(shifts['startTime'])
	shifts.set_index('playerId',inplace=True)

	# calculate the "event for" indicator
	oniceevent,eventforind=calceventforind(livefeed,shifts,playtype)

	# calculate event for/against count
	oniceevent['eventfor']=np.where(eventforind,1,0)
	oniceevent['eventagainst']=np.where(eventforind,0,1)
	foragainst=oniceevent[['eventfor','eventagainst']].groupby(level=['playerId']).sum()

	# calculate and merge in time-on-ice
	timeonice=shifts[['durationmin']].groupby(level=['playerId']).sum()
	foragainst=foragainst.join(timeonice,how='outer')
	foragainst['eventfor']=np.where(pd.isnull(foragainst['eventfor']),0,foragainst['eventfor'])
	foragainst['eventagainst']=np.where(pd.isnull(foragainst['eventagainst']),0,foragainst['eventagainst'])

	# calculate events for and against per 60min
	foragainst['eventfor60']=np.where(foragainst['durationmin']>0,
			60*foragainst['eventfor']/foragainst['durationmin'],0)
	foragainst['eventagainst60']=np.where(foragainst['durationmin']>0,
			60*foragainst['eventagainst']/foragainst['durationmin'],0)

	# calculate share of events (with -1 as value for no-event folks)
	foragainst['eventsharefor']=np.where(foragainst['eventfor']+foragainst['eventagainst']>0,
			foragainst['eventfor']/(foragainst['eventfor']+foragainst['eventagainst']),-1)
	foragainst['eventshareagainst']=np.where(foragainst['eventfor']+foragainst['eventagainst']>0,
			foragainst['eventagainst']/(foragainst['eventfor']+foragainst['eventagainst']),-1)

	return(foragainst)





