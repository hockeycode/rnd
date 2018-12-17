#############################################################
# Get the structure of json data (as interpreted by python)
# and write a memo
#############################################################
import requests
import json
import codecs


#############################################################
# writes metadata from an endnode
#############################################################
def endnode(myobj,myfile,inittxt):
	if type(myobj) in [int,float]:
		leaftxt=repr(myobj)
	elif type(myobj)==bool:
		leaftxt=repr(myobj)
	elif len(myobj)<=20:
		leaftxt=repr(myobj)
	else:
		leaftxt=repr(myobj[0:20])
	myfile.write(inittxt+repr(type(myobj))+', sample data: '+leaftxt+'\n')
	return(0)

	
#############################################################
# crawls through json data to pull the structure
#############################################################
def jsoncrawler(thisdict,leadingspaces='',keylist='',maxleaves=30,omitaway=True):
	# jsoncrawler iterates through json data
	# leaves are the keys of a dictionary within a given
	# level of json data

	leaves=thisdict.keys()

	# trim the number of leaves if there are too many, and report the data
	if len(leaves)>maxleaves:
		myfile.write(leadingspaces+repr(leaves)+'\n')
		myfile.write(leadingspaces+'Report truncated at '+repr(maxleaves)+' leaves'+'\n')
		leaves=leaves[0:maxleaves] 
	else:
		myfile.write(leadingspaces+repr(leaves)+'\n')

	# everything is just repeated for home and away, so drop the
	# away level
	if 'away' in leaves and omitaway:
		leaves.remove('away')

	for leaf in leaves:
		if isinstance(thisdict[leaf],dict):
			myfile.write('\n')
			#myfile.write(leadingspaces+keylist+'['+repr(leaf)+']'+'**********************************'+'\n')
			myfile.write(leadingspaces+'*********************************************************************'+'\n')
			myfile.write(leadingspaces+keylist+'['+repr(leaf)+'] is a dictionary with '+repr(len(thisdict[leaf]))+' keys:'+'\n')
			jsoncrawler(thisdict[leaf].copy(),leadingspaces+'    ',keylist+'['+repr(leaf)+']',maxleaves)

		elif isinstance(thisdict[leaf],list):
			myfile.write('\n')
			myfile.write(leadingspaces+'*********************************************************************'+'\n')
			#myfile.write(leadingspaces+keylist+'['+repr(leaf)+']'+'**********************************'+'\n')
			myfile.write(leadingspaces+keylist+'['+repr(leaf)+'] is a list with '+repr(len(thisdict[leaf]))+' levels:'+'\n')
			thislist=thisdict[leaf]
			firstitems=''
			while isinstance(thislist,list) and len(thislist)>0:
				thislist=thislist[0]
				firstitems=firstitems+'[0]'
			if isinstance(thislist,dict):
				myfile.write(leadingspaces+keylist+'['+repr(leaf)+']'+firstitems+'**********************************'+'\n')
				myfile.write(leadingspaces+keylist+'['+repr(leaf)+']'+firstitems+' is a dictionary with '+repr(len(thislist))+' keys:'+'\n')
				jsoncrawler(thislist,leadingspaces+'    ',keylist+'['+repr(leaf)+']'+firstitems,maxleaves)
			else:
	 			endnode(thislist,myfile,leadingspaces+keylist+'['+repr(leaf)+']'+firstitems+': ')

		else:
 			endnode(thisdict[leaf],myfile,leadingspaces+keylist+'['+repr(leaf)+']: ')


# sample code
# the highest-level information, but might not give all the 
# possible levels/keys
#r=h.pulldown(outfile=dataloc+'/testlivefeed')
#myfile=open(outloc+'/json_master.txt', 'w')
#rawobj=r.copy()
#branch=jsoncrawler(rawobj,maxleaves=10)
#myfile.close()


# drill down in select places
#myfile=open(outloc+'/json_drilldown.txt', 'w')
#rawobj=r.copy()

#branch=jsoncrawler(rawobj[u'liveData'][u'boxscore'][u'teams'][u'home'][u'teamStats'][u'teamSkaterStats'],
#	leadingspaces='                        ',keylist="[u'liveData'][u'boxscore'][u'teams'][u'home'][u'teamStats'][u'teamSkaterStats']",
#	maxleaves=30)
#myfile.write('\n\n\n')

#branch=jsoncrawler(rawobj[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8473563'],
#	leadingspaces='                        ',keylist="[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8473563']",
#	maxleaves=30)
#myfile.write('\n\n\n')

#branch=jsoncrawler(rawobj[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8468498'],
#	leadingspaces='                        ',keylist="[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8468498']",
#	maxleaves=30)
#myfile.write('\n\n\n')

#branch=jsoncrawler(rawobj[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8475831'],
#	leadingspaces='                        ',keylist="[u'liveData'][u'boxscore'][u'teams'][u'away'][u'players'][u'ID8475831']",
#	maxleaves=30)
#myfile.write('\n\n\n')
#myfile.close()

#rawobj=r.copy()
#nplays=len(rawobj[u'liveData'][u'plays'][u'allPlays'])
#print(nplays)

#eventtypes=[]
#for x in rawobj[u'liveData'][u'plays'][u'allPlays']:
#	eventtypes.append(x[u'result'][u'eventTypeId'])
#eventtypes=list(set(eventtypes))
#print(eventtypes)

#myfile=open(outloc+'/json_plays.txt','w')
#for ii in range(0,len(rawobj[u'liveData'][u'plays'][u'allPlays']),1):
#	if rawobj[u'liveData'][u'plays'][u'allPlays'][ii][u'result'][u'eventTypeId'] in eventtypes:
#		eventtypes.remove(rawobj[u'liveData'][u'plays'][u'allPlays'][ii][u'result'][u'eventTypeId'])
#		branch=jsoncrawler(rawobj[u'liveData'][u'plays'][u'allPlays'][ii],
#			leadingspaces='',keylist="[u'liveData'][u'plays'][u'allPlays'][ii]",
#			maxleaves=30)
#		myfile.write('\n\n\n')

#myfile.close()


