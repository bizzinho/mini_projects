# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 18:28:35 2019

@author: Dave
"""

import urllib3
from bs4 import BeautifulSoup

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, median_absolute_error
from sklearn.preprocessing import StandardScaler

def getResults(estimator, X, Y, incomingax = None, returnAx = False):
    
    Ypred = estimator.predict(X).ravel()
    if incomingax is None:
        _, ax = plt.subplots(1,2)
    else:
        ax = incomingax
    ax[0].plot(Y, Ypred, 'o')
    ax[0].plot([Y.min(), Y.max()],[Y.min(), Y.max()],'k--')
    ax[0].set_xlabel("Observed Price k€")
    ax[0].set_ylabel("Predicted Price k€")
    
    ax[1].scatter(sorted(Ypred),[x for _,x in sorted(zip(Y,Ypred-Y))])
    if incomingax is None:
        ax[1].plot(Y,np.zeros(Y.shape),'k--')
    ax[1].set_xlabel("Predicted Price k€")
    ax[1].set_ylabel("Residual k€")
    plt.tight_layout()
    plt.show()
    r2 = r2_score(Y, Ypred)
    MAE = median_absolute_error(Y, Ypred)
    
    # compute mean absolute percentage error (MAPE)
    MAPE = np.mean(np.abs(Y - Ypred) / Y * 100)
    
    if returnAx == False:
        return r2, MAE, MAPE
    else:
        return r2, MAE, MAPE, ax
    
def myImpute(df_org, how = 'median'):
    
    df = df_org.copy()
    
    if (type(how) == str) and (how == 'median'):
        df = df.fillna(df.median())
    elif (type(how) == str) and (how == 'mean'):
        df = df.fillna(df.mean())
    elif (type(how) == str) and (how == 'mode'):
        df = df.fillna(df.mode()[0])
    else:
        df = df.fillna(how)
        
    return df


mydf = pd.read_excel('Apartment_PT.xlsx', sheet_name=0)
mydf = mydf[mydf.Outlier == 'No']
mydf = mydf.reset_index(drop = True)

X = mydf.copy()


orientations = ['E','N','S','W']
for o in orientations:
    X[o] = X.Orientation.str.contains(o, na=False)
    

X.drop(columns=['Link', 'Date Found', 'Beach Distance', "Ria Distance", "Orientation"], inplace= True)

Y = pd.DataFrame(X.pop('Price k$'))

X.Floor = pd.to_numeric(X.Floor.apply(lambda x: str(x).split('-')[-1]),errors='coerce')

# fill in median age for year and floor
X[['Year Built','Floor']] = myImpute(X[['Year Built','Floor']], how = 'median')

X['Lote'] = myImpute(X['Lote'],0)

#average reduction from bruto to uteis size
fac = (X['Size (Uteis)'] / X['Size']).median()

X['Size (Uteis)'] = myImpute(X['Size (Uteis)'], X['Size']*fac)

X['Energy Certificate'] = myImpute(X['Energy Certificate'], 'mode')

X[['Garage', 'Elevator','AC','Solar Panels','Piscina','Veranda','Terrace','Built-in Closets']] = myImpute(X[['Garage', 'Elevator','AC','Solar Panels','Piscina','Veranda','Terrace','Built-in Closets']], 'No')

myCats = ['Beach','Type','Energy Certificate', 'Garage', 'Elevator','AC','Solar Panels','Piscina','Veranda','Terrace','Built-in Closets','Seaview','Riaview']

X[myCats] = X[myCats].astype('category')

X = pd.get_dummies(X, drop_first = True)

Xm = X.to_numpy(dtype='float64')
xcols = X.columns.values
Ym = Y.to_numpy(dtype='float64').ravel()

scaler_all = StandardScaler()
X0 = scaler_all.fit_transform(Xm)
pca = PCA(n_components = 2)
XS = pca.fit_transform(X0)
plt.figure()
loadings = pca.components_.T
for loading,col in zip(loadings,xcols):
    plt.annotate(col,loading)
plt.xlim((np.min(loadings[:,0])-0.5,np.max(loadings[:,0])+0.5))
plt.ylim((np.min(loadings[:,1])-0.5,np.max(loadings[:,1])+0.5))
plt.figure()
for i, score in enumerate(XS):
    plt.annotate(i,score)
plt.xlim((np.min(XS[:,0])-0.5,np.max(XS[:,0])+0.5))
plt.ylim((np.min(XS[:,1])-0.5,np.max(XS[:,1])+0.5))

X_train, X_test, Y_train, Y_test = train_test_split(Xm, Ym,test_size = 0.15, stratify = mydf.Beach)
scaler = StandardScaler()
X0_train = scaler.fit_transform(X_train)
X0_test = scaler.transform(X_test)

## PLS
pls = PLSRegression(2)
pls.fit(X0_train, Y_train)

print("PLS Model")
print("Train")
r2, MAE, MAPE, ax = getResults(pls, X0_train, Y_train, returnAx = True)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))
print("Test")
r2, MAE, MAPE = getResults(pls, X0_test, Y_test, incomingax = ax)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))

## Elastic Net
eln = ElasticNet(l1_ratio=0.5)
eln.fit(X0_train, Y_train)
print("Elastic Net")
print("Train")
r2, MAE, MAPE, ax = getResults(eln, X0_train, Y_train, returnAx = True)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))
print("Test")
r2, MAE, MAPE = getResults(eln, X0_test, Y_test, incomingax = ax)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))
sys.exit()
# RF
estilist = np.linspace(10,500,5)
mdlist = np.arange(5,6)

kf = KFold(shuffle = True, n_splits = 10)

r2s = np.zeros((len(estilist),len(mdlist),kf.get_n_splits()))
maes = np.zeros((len(estilist),len(mdlist),kf.get_n_splits()))
for i, estis in enumerate(estilist):
    for j, maxdis in enumerate(mdlist):
        RF = RandomForestRegressor(n_estimators = int(estis), max_depth = maxdis)
        # RF.fit(X_train,Y_train)
        
        # yhat_test = RF.predict(X_test)
        # maes[i,j] = mean_absolute_error(Y_test,yhat_test)
        result = cross_validate(RF, X = X_train, y = Y_train, scoring = ['neg_median_absolute_error','r2' ], cv = kf)
        r2s[i,j,:] = result['test_r2']
        maes[i,j,:] = result['test_neg_median_absolute_error']

avgR2s = np.mean(r2s,axis=2)
avgMaes = np.mean(maes,axis=2)
bestCombo = np.unravel_index(np.argmax(avgMaes),avgMaes.shape)

RF = RandomForestRegressor(n_estimators = 50, max_depth = 3)
# RF = RandomForestRegressor(n_estimators = int(estilist[bestCombo[0]]), max_depth = mdlist[bestCombo[1]])
RF.fit(X_train,Y_train)

print('Random Forest')
print("Train")
r2, MAE, MAPE, ax= getResults(RF, X_train, Y_train, returnAx = True)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))
print("Test")
r2, MAE, MAPE = getResults(RF, X_test, Y_test, incomingax = ax)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))

mydf['predPrice'] = RF.predict(Xm)
mydf['spread'] = mydf['Price k$'] - mydf['predPrice'] # a positive spread means bad deal
mydf.sort_values(by = 'spread')
mydf = mydf.sort_values(by = 'spread')