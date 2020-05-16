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

from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

def getResults(estimator, X, Y):
    
    Ypred = estimator.predict(X).ravel()
    
    plt.plot(Y, Ypred, 'o')
    plt.plot([Y.min(), Y.max()],[Y.min(), Y.max()],'--')
    ax = plt.gca()
    ax.set_xlabel("Observed Price k€")
    ax.set_ylabel("Predicted Price k€")
    plt.show()
    r2 = r2_score(Y, Ypred)
    MAE = mean_absolute_error(Y, Ypred)
    
    # compute mean absolute percentage error (MAPE)
    MAPE = np.mean(np.abs(Y - Ypred) / Y * 100)
    
    return r2, MAE, MAPE

    
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

X = pd.get_dummies(X)

Xm = X.to_numpy(dtype='float64')
Ym = Y.to_numpy(dtype='float64').ravel()

pls = PLSRegression(2)
pls.fit(Xm, Ym)

print("PLS Model")
r2, MAE, MAPE = getResults(pls, Xm, Ym)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))

## Elastic Net
X0m = StandardScaler().fit_transform(Xm)
eln = ElasticNet(l1_ratio=0.5)
eln.fit(X0m, Ym)
print("Elastic Net")
r2, MAE, MAPE = getResults(eln, X0m, Ym)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))

# RF
RF = RandomForestRegressor(n_estimators = 30)
RF.fit(Xm,Ym)
print('Random Forest')
r2, MAE, MAPE = getResults(RF, Xm, Ym)
print("R2= {:4.2f}; MAE={:4.2f}k Euros; MAPE = {:4.1f}%".format(r2, MAE, MAPE))