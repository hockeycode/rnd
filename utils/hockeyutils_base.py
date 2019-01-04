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












def getstickyindexold2(constructor,moreconstructor,indexp,ii):
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

def deepdivewithindexold2(constructor,p,indexp,ii=0,forkpoint=None):
	if forkpoint is None:
		forkpoint=0
		for ik in range(min(len(p),len(indexp))-1):
			if indexp[ik+1]==p[ik+1]:
				forkpoint=forkpoint+1

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









def getstickyindexold(constructor,indexp,ii):
	stickyindex=[]
	stickyindex=constructor
	for ik in range(ii+1,len(indexp),1):
		if indexp[ik]=='ij':
			print('error at '+repr(ik))
		else:
			stickyindex=stickyindex[indexp[ik]]
	return(stickyindex)

def deepdivewithindexold(constructor,p,indexp,ii=0,stickyindex=None,forkpoint=None):
	if forkpoint is None:
		forkpoint=0
		for ik in range(min(len(p),len(indexp))-1):
			if indexp[ik+1]==p[ik+1]:
				forkpoint=forkpoint+1

	if ii<len(p)-1:
		if p[ii]=='ij':
			newconstructor=[]
			for ik in range(len(constructor)):
				moreconstructor=deepdivewithindex(constructor[ik],p,indexp,ii+1,stickyindex=stickyindex,forkpoint=forkpoint)
				if ii==forkpoint:
					stickyindex=getstickyindex(constructor[ik],indexp,ii)
					for im in range(len(moreconstructor)):
						if type(moreconstructor[im])==dict:
							moreconstructor[im]['stickyindex']=stickyindex
						else:
							moreconstructor[im]={'values':moreconstructor[im],'stickyindex':stickyindex}
				newconstructor.extend(moreconstructor)
		else:
			moreconstructor=deepdivewithindex(constructor[p[ii]],p,indexp,ii+1,stickyindex=stickyindex,forkpoint=forkpoint)
			if ii==forkpoint:
				stickyindex=getstickyindex(constructor,indexp,ii)
				for im in range(len(moreconstructor)):
					if type(moreconstructor[im])==dict:
						moreconstructor[im]['stickyindex']=stickyindex
					else:
						moreconstructor[im]={'values':moreconstructor[im],'stickyindex':stickyindex}
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


