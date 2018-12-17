import numpy as np
import pandas as pd
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.collections import PatchCollection


##########################################################
# 1. set plot to match rink dimensions
##########################################################
def rinkaxes(makefig=True,ax=[],adj=1):
	if makefig:
		f=plt.figure(figsize=(adj*5,adj*2.05))
		ax=f.add_subplot(111)
	else:
		f=False
	
	ax.set_xlim(left=-100,right=100)
	ax.set_ylim(bottom=-42.5,top=42.5)

	return(f,ax)

##########################################################
# 2. draw rink markings
##########################################################
def rinkmarkings(ax):

	# draw lines
	for xl in [-89,-25,0,25,89]:
		plt.plot([xl,xl],[-42.5,42.5],'k-')

	# draw circles
	patches=[Circle((0,0),15),Circle((-69,-22),15),Circle((-69,22),15),Circle((69,-22),15),Circle((69,22),15)]
	p=PatchCollection(patches)
	p.set_edgecolor('black')
	p.set_facecolor('none')
	ax.add_collection(p)
	
	return(0)



##########################################################
# 3. heatmap on rink
##########################################################

def heatmap(xy,plottitle='Heatmap',adj=1):
	# fit the kernel density with sklearn
	params={'bandwidth':np.logspace(-1,1,20)}
	grid=GridSearchCV(KernelDensity(),params,cv=5)
	grid.fit(xy)
	print('best bandwidth: {0}'.format(grid.best_estimator_.bandwidth))
	mymodel=grid.best_estimator_

	# sample for scoring the resulting kernel density
	scoringsample=pd.DataFrame([[x,y] for x in range(-100,101,1) for y in range (-42,43)])

	# score the samples and format for plotting
	scored=mymodel.score_samples(scoringsample)
	scored=scored.reshape([201,85])
	scored=scored.transpose()

	# plot the heatmap on a rink
	f,ax=rinkaxes(makefig=True,adj=adj)
	plt.contourf(range(-100,101,1),range(-42,43,1),scored)

	# add markings
	rinkmarkings(ax)
	plt.title('Kernel-smoothed distribution, b='+repr(grid.best_estimator_.bandwidth))

	return(grid.best_estimator_.bandwidth)

