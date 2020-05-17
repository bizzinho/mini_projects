# -*- coding: utf-8 -*-
"""
Created on Sun May 17 11:23:23 2020

@author: Dave
"""

import numpy as np
import pandas as pd
import seaborn as sns

beachCols = {x.split('Beach_')[1]:i for i,x in enumerate(xcols) if 'beach' in x.lower()}
nBeaches = len(beachCols.keys())

sampleSize = 100
randomRows = np.random.choice(Xm.shape[0], sampleSize, replace=False)
sample = Xm[randomRows,:]

Y_itFactor = pd.DataFrame(columns = ['ID','Beach','Price'])

for beach, thisCol in beachCols.items():
    df_loc = pd.DataFrame(columns = Y_itFactor.columns)
    notThisBeach = [col for col in beachCols.values() if col != thisCol]
    sample[:,thisCol] = True
    sample[:,notThisBeach] = False
    
    df_loc['Price'] = RF.predict(sample)
    df_loc['Beach'] = beach
    df_loc['ID'] = randomRows
    
    Y_itFactor = Y_itFactor.append(df_loc, ignore_index = True)
plt.figure()
sns.boxplot(data = Y_itFactor, x = 'Beach', y = 'Price')
compare = Y_itFactor.pivot(columns = 'Beach',values = 'Price',index = 'ID')
compare['CN-Barra'] = compare['Costa Nova'] - compare['Barra']
plt.figure()
sns.distplot(compare['CN-Barra'])
