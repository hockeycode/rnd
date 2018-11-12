import pandas as pd
from pandas.io.json import json_normalize
import numpy as np 
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
##########################################################
# this does variable cleaning for some standard variables
# in the nhl api, including dealing with some quirks 
# that don't neatly align with built-in python/numpy
# functions
##########################################################
def stringtominutes(t):
	# takes MMMM:SS (arbitrary number of minutes) and yields MMMMM.MMMMM
	if pd.isnull(t):
		s=[0,0]
	else:
		s=t.split(':')
	return(float(s[0])+float(s[1])/60.0)
stringtominutesv=np.vectorize(stringtominutes)
def strtoinches(t):
	# takes X" Y' and converts to inches only
	if pd.isnull(t):
		return(0)
	elif t=='':
		return(0)
	else:
		u=t.split("' ")
		u[1]=u[1].replace("\"","")
		return(12*float(u[0])+float(u[1]))
strtoinchesv=np.vectorize(strtoinches)

def getyear(t):
	if pd.isnull(t):
		return(0)
	elif t=='':
		return(0)
	else:
		return(int(t[0:4]))
getyearv=np.vectorize(getyear)

def countrybkt(x):
	if x=='CAN':
		y='CAN'
	elif x=='CZE':
		y='CZE'
	elif x=='FIN':
		y='FIN'
	elif x=='RUS':
		y='RUS'
	elif x=='SWE':
		y='SWE'
	elif x=='USA':
		y='USA'
	else:
		y='OTH'
	return(y)
countrybktv=np.vectorize(countrybkt)

def cleantime(df,stem=''):
	# time variables
	df[stem+'timeOnIce']=stringtominutesv(df[stem+'timeOnIce'])
	df[stem+'timeOnIcePerGame']=stringtominutesv(df[stem+'timeOnIcePerGame'])
	df[stem+'evenTimeOnIce']=stringtominutesv(df[stem+'evenTimeOnIce'])
	df[stem+'evenTimeOnIcePerGame']=stringtominutesv(df[stem+'evenTimeOnIcePerGame'])
	df[stem+'powerPlayTimeOnIce']=stringtominutesv(df[stem+'powerPlayTimeOnIce'])
	df[stem+'powerPlayTimeOnIcePerGame']=stringtominutesv(df[stem+'powerPlayTimeOnIcePerGame'])
	df[stem+'shortHandedTimeOnIce']=stringtominutesv(df[stem+'shortHandedTimeOnIce'])
	df[stem+'shortHandedTimeOnIcePerGame']=stringtominutesv(df[stem+'shortHandedTimeOnIcePerGame'])
	return(df)

def cleanstr(df):
	df['birthCountry2']=countrybktv(df['birthCountry'])
	df['nationality2']=countrybktv(df['nationality'])
	return(df)


def cleanother(df):
	df['alternateCaptain']=(df['alternateCaptain']==True)
	df['captain']=(df['captain']==True)

	# height,birthDate	
	df['height']=strtoinchesv(df['height'])
	df['birthyear']=getyearv(df['birthDate'])
	df['age']=df.index.get_level_values('season')%10000-df['birthyear']

	# convert shots into shots per game to deal with collinearity
	df['shotspergame']=df['shots']/df['games']
	df['shotspergame'].fillna(0,inplace=True)
	return(df)
