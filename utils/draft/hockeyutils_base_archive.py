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
# because this is designed for pulling large amounts of data
#
# for analysis, when there are both "one" and "multi" options,
# it covers only the "multi" option. For example, there are
# options to pull one team's information or all teams' 
# information. I have only coded the latter.
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
def batchrename(currentvars,categories,stem=''):

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
			'team.name':'t.name'
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


	# select entries and add the stem (if selected)
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
	print(' ')
	print(df.dtypes)	
	print(' ')

	if morerename is not None:
		df.rename(columns=morerename,inplace=True)

	if dropvars is not None:
		df.drop(columns=dropvars,inplace=True)

	if indexvar is not None:
		df.set_index(indexvar,inplace=True)
	
	return(df)


##############################################################
# (5) Process team data from a pull like this:
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

	# move to standardized short names
	#renamedict=batchrename(df.keys(),
	#	['franchise','venue','conference','division','team2'],
	#	stem=stem)
	#df.rename(columns=renamedict,inplace=True)
	#df.rename(columns={'id':'teamid'},inplace=True)

	# there are two columns with franchise ID; drop one of them
	#df.drop(columns=['franchid2'],inplace=True)

	# add the primary key
	#df.set_index(['teamid'],inplace=True)

	# write to csv if requested
	if outcsv is not None:
		df.to_csv(path_or_buf=outcsv+'.csv',encoding='utf-8')

	return(df)


##############################################################
# (6) Process team stats (all teams/one season) from this pull:
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
	
	# move to standardized short names
	#renamedict=batchrename(dfteam.keys(),
	#	['franchise','venue','conference','division','team2'],
	#	stem=stem)
	#dfteam.rename(columns=renamedict,inplace=True)
	#dfteam.rename(columns={'id':'teamid'},inplace=True)

	# there are two columns with franchise ID; drop one of them
	#dfteam.drop(columns=['teamStats','franchid2'],inplace=True)

	# add the primary key
	#dfteam.set_index(['teamid'],inplace=True)

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
	print(dfn.dtypes)

	# there are two columns with team ID; drop one of them
	#dfn.drop(columns=['team.id'],inplace=True)
	#dfrank.drop(columns=['team.id'],inplace=True)

	# add the primary key
	#dfn.set_index(['teamid'],inplace=True)
	#dfrank.set_index(['teamid'],inplace=True)

	# move to standardized short names
	#renamedict=batchrename(dfn.keys(),['team'],stem=stem)
	#dfn.rename(columns=renamedict,inplace=True)
	#dfrank.rename(columns=renamedict,inplace=True)



	dfteam=polish(dfn,
		renamecat=['team'],
		indexvar=['teamid'],
		stem=stem)
	dfrank=polish(dfn,
		renamecat=['team'],
		indexvar=['teamid'],
		stem=stem)




	if outcsv is not None:
		dfteam.to_csv(path_or_buf=outcsv+'_team.csv',encoding='utf-8')
		dfn.to_csv(path_or_buf=outcsv+'_n.csv',encoding='utf-8')
		dfrank.to_csv(path_or_buf=outcsv+'_rank.csv',encoding='utf-8')

	return(dfteam,dfn,dfrank)


##############################################################
# (7) Process team rosters (all teams/one season) from this pull:
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

	# move to standardized short names
	#renamedict=batchrename(dfteam.keys(),
	#	['franchise','venue','conference','division','team2'],
	#	stem=stem)
	#dfteam.rename(columns=renamedict,inplace=True)
	#dfteam.rename(columns={'id':'teamid','roster.link':'r.link'},inplace=True)

	# there are two columns with franchise ID; drop one of them
	#dfteam.drop(columns=['roster.roster','franchid2'],inplace=True)

	# add the primary key
	#dfteam.set_index(['teamid'],inplace=True)

	dfteam=polish(dfteam,
		renamecat=['franchise','venue','conference','division','team2'],
		indexvar=['teamid'],
		morerename={'id':'teamid','roster.link':'r.link'},
		dropvars=['roster.roster','franchid2'],
		stem=stem)




	return(dfteam)




	
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
def pivotlist(outerlist,metrickeys,cat,stemdict,primarykeylist=None):
	transposed=[]
	for ii in range(len(outerlist)):
		onerow={stemdict[y[cat]]+m:y[m] for y in outerlist[ii] for m in metrickeys}
		if primarykeylist is not None:
			print('is not none')
			onerow['primarykey']=primarykeylist[ii]
		transposed.append(onerow)
	return(transposed)




