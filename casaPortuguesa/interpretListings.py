# -*- coding: utf-8 -*-
"""
Created on Sun May  3 18:01:12 2020

@author: Dave
"""
import pandas as pd
import os
from bs4 import BeautifulSoup

def findInfo(totalString, nearPattern, distance = 1, direction = 'after', lenOutput = 1, castTo = None):
    numberOfWordsInPattern = len(nearPattern.split())
    
    myString = totalString
    value = None
    notDone = True
    
    while (myString.count(nearPattern) > 0) and (notDone == True):
        idx = myString.find(nearPattern)
        if direction == 'after':
            candidate_value = myString[idx:].split()[numberOfWordsInPattern + distance - 1:numberOfWordsInPattern + distance + lenOutput - 1]
        elif direction == 'before':
            if lenOutput != 1:
                raise NotImplementedError()
            candidate_value = [myString[:idx].split()[-distance]]
        
        if castTo == 'int':
            try:
                value = int(candidate_value[0])
                notDone = False
            except:
                pass    
        elif castTo == 'float':
            try:
                value = float(candidate_value[0])
                notDone = False
            except:
                pass
        elif castTo is None:
            value = candidate_value
            notDone = False
        
        if notDone == True:
            myString = myString[idx+len(nearPattern):]

    return value

def cleanString(myText):
    myText = myText.replace('/',' ').replace('º','').replace('²','2')
    myText = "".join(e for e in myText if (e.isalnum() or e == ' ')) # only alphanumeric (no brackets or punctuation)
    myText = " ".join(myText.split()) # remove double spaces, etc.
    myText = myText.lower() # no capitalization
    myText = myText.replace('ã','a').replace('é','e').replace('ê','e').replace('í','i').replace('ç','c').replace('á','a').replace('ú','u') # remove chars with accents
    
    return myText

# add new listings in DB
df = pd.read_excel('Apartment_PT.xlsx',index_col = 0,
                   sheet_name = 'DB')
os.system('copy Apartment_PT.xlsx Apartment_PT_{}.xlsx'.format(pd.Timestamp.now().strftime('%d%b%Y')))

df_new = pd.DataFrame(columns = df.columns)
df_new.index.name = df.index.name
moveFile = []

fnames = [file for file in os.listdir('./pages_html/') if (file!='done') and (file.endswith('.html'))]
# go over all new html files that haven't been read out yet (are not in folder 'done')
for fname in fnames:
    # read file in
    with open('./pages_html/'+fname,'r',encoding="utf-8") as f:
        page = f.read()
    soup = BeautifulSoup(page, features="html.parser")
    
    # remember ID
    ID = 'IDEALISTA_'+fname[:-15]
    print("ID = {}".format(ID))
    
    beachText = cleanString(soup.find('a',{'class':'btn nav back icon-arrow-double-left'}).text)
    if 'nazare' in beachText:
        beach = 'Barra'
    elif 'encarnacao' in beachText:
        beach = 'Costa Nova'
    elif 'boa hora' in beachText:
        beach = 'Vagueira'
    
    # find price
    price = float(soup.find('span',attrs = {'class':'info-data-price'}).text.replace('€',''))
    
    # size 
    size = float(soup.find('div',attrs = {'class':'info-features'}).text.split('m² construídos')[0].split()[-1])
    
    # bedrooms
    for info in soup.find('div',attrs = {'class':'info-features'}).find_all('span')[::-1]:
        if (len(info.text) == 2) and (info.text.startswith('T')):
            bedrooms = int(info.text[1])
            break
    
    # date found (is in the filename)
    dateFound = pd.to_datetime(fname[-14:-5])
    
    # link (can be created knowing the ID)
    link = 'https://www.idealista.pt/imovel/'+fname[:-15]+'/'
    
    myText = soup.find('span',{'class':'main-info__title-main'}).get_text(separator=' ') + \
            soup.find('div',{'class':'comment'}).get_text(separator=' ') + \
            soup.find('div',{'class':'details-property'}).get_text(separator=' ')
    
    # clean up the string a bit
    myText = cleanString(myText)
    
    # year built
    year = findInfo(myText,'construido em', castTo = 'int')
            
    # type   
    if ('moradia' in myText) and ('apartamento' in myText):
        print('The words moradia and apartamento occurred in the text, I set type to "Apartment".')
        myType = 'Apartment'
    elif ('apartamento' in myText): 
        myType = 'Apartment'
    elif (('moradia' in myText) or ('casa' in myText)):
        myType = 'House'
    else:
        myType = None
        
    # bathrooms
    bathrooms = findInfo(myText,'casas de banho', direction = 'before', castTo = 'int')
    if bathrooms is None:
        bathrooms = findInfo(myText,'casa de banho', direction = 'before', castTo = 'int')    
        
    # garage
    if ('garagem' in myText) and ('estacionamento' in myText):
        print('The words garagem and estacionamento occurred in the text, I set "Garage" to "Yes".')
        garage = 'Yes'
    elif ('garagem' in myText): 
        garage = 'Yes'
    elif ('estacionamento' in myText):
        garage = 'Outside'
    else:
        garage = 'No'
        
    # swimming pool
    if ('piscina' in myText):
        piscina = 'Yes'
    else:
        piscina = 'No'
        
    # veranda
    if ('varanda' in myText):
        veranda = 'Yes'
    else:
        veranda = 'No'
        
    # veranda
    if ('terraco' in myText):
        terrace = 'Yes'
    else:
        terrace = 'No'
        
    wordsAfterVista = findInfo(myText,'vista',lenOutput = 7)
    if wordsAfterVista is not None:
        if 'mar' in wordsAfterVista:
            seaView = 'Yes'
        else:
            seaView = 'No'
        
        if 'ria' in wordsAfterVista:
            riaView = 'Yes'
        else:
            riaView = 'No'
    else:
        riaView = 'No'
        seaView = 'No'
        
    if 'armarios embutidos' in myText:
        builtInClosets = 'Yes'
    else:
        builtInClosets = 'No'
        
    if ('elevador' in myText) and ('sem elevador' not in myText):
        elevator = 'Yes'
    else:
        elevator = 'No'
    
    if 'ar condicionado' in myText:
        ac = 'Yes'
    else:
        ac = 'No'
    
    sizeUteis = findInfo(myText,'m2 uteis', direction = 'before', castTo = 'int')
    
    lote = findInfo(myText,'lote de', direction = 'after', castTo = 'int')
    
    if myType == 'Apartment':
        floor = findInfo(myText,'andar', direction = 'before', castTo = 'int')
        if (floor is None) and ('res do chao' in myText):
            floor = 0
    else:
        floor = findInfo(myText,'andares',direction = 'before', castTo = 'int')
    
    if 'paineis solares' in myText:
        solar = 'Yes'
    else:
        solar = 'No'
    
    orientation = []
    wordsAfterOrientation = findInfo(myText,'orientacao', lenOutput = 7)
    if wordsAfterOrientation is not None:
        if 'norte' in wordsAfterOrientation:
            orientation.append('N')
        if 'sul' in wordsAfterOrientation:
            orientation.append('S')
        if ('este' in wordsAfterOrientation) or ('nascente' in wordsAfterOrientation):
            orientation.append('E')
        if ('oeste' in wordsAfterOrientation) or ('poente' in wordsAfterOrientation):
            orientation.append('W')
        
    energyRating = soup.find('span', {'class':lambda x: x and x.startswith('icon-energy')})
    if energyRating is not None:
        energyRating = energyRating['title'].upper()
    else:
        if 'propriedade isenta' in myText:
            energyRating = 'Excempt'
    
    df_new.loc[ID,'Beach'] = beach
    df_new.loc[ID,'Type'] = myType
    df_new.loc[ID,'Price k$'] = price
    df_new.loc[ID,'Size'] = size
    df_new.loc[ID,'Size (Uteis)'] = sizeUteis
    df_new.loc[ID,'Lote'] = lote
    df_new.loc[ID,'Bedrooms'] = bedrooms
    df_new.loc[ID,'Bathrooms'] = bathrooms
    df_new.loc[ID,'Year Built'] = year
    df_new.loc[ID,'Garage'] = garage
    df_new.loc[ID,'Date Found'] = dateFound
    df_new.loc[ID,'Floor'] = floor
    df_new.loc[ID,'Elevator'] = elevator
    df_new.loc[ID,'Energy Certificate'] = energyRating
    df_new.loc[ID,'AC'] = ac
    df_new.loc[ID,'Solar Panels'] = solar
    df_new.loc[ID,'Piscina'] = piscina
    df_new.loc[ID,'Veranda'] = veranda
    df_new.loc[ID,'Terrace'] = terrace
    df_new.loc[ID,'Built-in Closets'] = builtInClosets
    df_new.loc[ID,'Seaview'] = seaView
    df_new.loc[ID,'Riaview'] = riaView
    df_new.loc[ID,'Beach Distance'] = None # XX
    df_new.loc[ID,'Ria Distance'] = None # XX
    df_new.loc[ID,'Orientation'] = ','.join(orientation) 
    df_new.loc[ID,'Link'] = link 
    
    moveFile.append(fname)

for f in moveFile:
    os.rename('./pages_html/'+f, './pages_html/done/'+f)
df_new.drop_duplicates()
print(df_new)
df = df.append(df_new, ignore_index = True)
df.to_excel('Apartment_PT.xlsx', index = False)

    # remaining entries: 
    # Lote, Energy Certificate, AC, Solar Panels, Orientation
    