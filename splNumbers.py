#from __future__ import print_function
import httplib2
import os
import pandas as pd
import numpy as np
import datetime as dt
import networkx as nx
import pdb

import plotly as py
import plotly.figure_factory as ff
import plotly.graph_objs as go

import pycountry
from collections import Counter

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from geopy.geocoders import Nominatim
geolocator = Nominatim()

from scopus import ScopusSearch
from scopus import ScopusAuthor

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1qUpuZdj8Tddw-ZMDo530JGWUC7Cz-vuRNGqPGNaNhgo'
    rangeName = 'Sheet1!A2:N77'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    
    df = pd.DataFrame(values[1:],columns=values[0])
    df.drop(["Completeness Check","Scholar link"],axis=1,inplace=True)
    
    df_total = df.copy()
    
    df.replace('',np.nan,inplace=True)
    df.dropna(inplace=True)
    
    df.replace('n/a',np.nan,inplace=True)
    df.replace('present',dt.datetime(2017,12,31),inplace=True)
    
    # rename colums
    colNames = df.columns.tolist()
    colNames[5] = 'Start Position'
    colNames[6] = 'End Position'
    colNames[7] = 'Start Master'
    colNames[8] = 'End Master'
    colNames[9] = 'Start PhD'
    colNames[10] = 'End PhD'
    df.columns = colNames
    
#    print(df)
    
    for i in range(5,11):
        #print(i)
        df.iloc[:,i] = pd.to_datetime(df.iloc[:,i])

    return df, df_total

def plotGantt(df):
    # all Position starts
    myPos = df[["Name","Start Position","End Position"]].copy()
    myPos['Resource'] = "Position"
    myPos.columns = ["Task","Start","Finish","Resource"]
    
    # all Master starts
    myMaster = df[["Name","Start Master","End Master"]].copy()
    myMaster['Resource'] = "Master"
    myMaster.columns = ["Task","Start","Finish","Resource"]
    
    # all Position starts
    myPhD = df[["Name","Start PhD","End PhD"]].copy()
    myPhD['Resource'] = "PhD"
    myPhD.columns = ["Task","Start","Finish","Resource"]
    
    myAll = myPos.append(myMaster).append(myPhD)
    
    myAll = myAll[myAll['Start'].notnull()].copy()
    myAll.sort_values("Start",inplace=True)
    myAll.reset_index(drop=True,inplace=True)

    fig = ff.create_gantt(myAll,colors = {'Position': 'rgb(220, 0, 0)','Master': (1, 0.9, 0.16),'PhD': 'rgb(0, 255, 100)'},index_col="Resource",group_tasks=True)
    py.offline.plot(fig)
    
def plotGraph():
    
    A2 = pd.read_excel('collaborators.xlsx')
    A = A2.as_matrix()[:,1:]
    A = np.nan_to_num(np.matrix(A).astype(float))
    
    hasCollabo = (np.sum(np.nan_to_num(A.astype(float)),axis=1)>0).A1
    
    Aloc = A[hasCollabo,:]
    A = Aloc[:,hasCollabo]
    
    myNames = A2.iloc[:,0].as_matrix()
    myNames = myNames[hasCollabo]
    
    G = nx.from_numpy_matrix(A)
    
    pos = nx.spring_layout(G)
    #pos = nx.get_node_attributes(G,'pos')
    
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=go.Line(width=0.5,color='#888'),
        hoverinfo='none',
        mode='lines')

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += [x0, x1, None]
        edge_trace['y'] += [y0, y1, None]
    
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        textposition='bottom',
        hoverinfo='text',
        text = myNames,
        marker=go.Marker(
            showscale=True,
            # colorscale options
            # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
            # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
            colorscale='YIGnBu',
            reversescale=True,
            color=[],
            size=20,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))

    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'].append(x)
        node_trace['y'].append(y)
        
    for node, adjacencies in enumerate(G.adjacency_list()):
        node_trace['marker']['color'].append(len(adjacencies))
        node_info = '# of connections: '+str(len(adjacencies))
        #node_trace['text'].append(node_info)
        
    fig = go.Figure(data=go.Data([edge_trace, node_trace]),
         layout=go.Layout(
            title='SPL Authorship Network',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=go.XAxis(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=go.YAxis(showgrid=False, zeroline=False, showticklabels=False)))

    py.offline.plot(fig)
    
def countNations(df,normalize=False):
    xx = df['Nationality'].str.split(',')
    xx.dropna(inplace=True)
    yy = [str.strip(item) for x in xx for item in x]
    
    listNationalities = [pycountry.countries.get(alpha_2 = country).alpha_3 for country in yy]
    natCount = Counter(listNationalities)
    if normalize == True:
        total = np.sum(list(natCount.values()))
        for key in natCount:
            natCount[key] = natCount[key]/total
    
    listNationalities = np.unique(listNationalities)
    zvalues = [natCount[nation] for nation in listNationalities]
    
    return listNationalities,zvalues,natCount

def plotMap(df,geoDict = None):

    listNationalities, zvalues,_ = countNations(df)

    baseMap = [go.Choropleth(locationmode = 'iso-3',
        locations = listNationalities,
        z = zvalues,
        showscale = False,
        geo = 'geo')]
    
    baseMap.append(go.Choropleth(locationmode = 'iso-3',
        locations = listNationalities,
        z = zvalues,
        showscale = False,
        geo = 'geo2'))
    
    
    if geoDict is None:
        allTowns = set(df['Home Town']).union(df['Current Town'])
        geoDict = {}
        for town in allTowns:
            print(town)
            myloc = geolocator.geocode(town,timeout=20)
            geoDict[town] =  dict(lon=myloc.longitude,lat = myloc.latitude)
    
    userGroups = []
    for _,homeCity,currentCity in df[['Home Town','Current Town']].itertuples():
        if homeCity is not np.nan:
            userGroup = dict(type='scattergeo',
                             lon = [geoDict[homeCity]['lon'],geoDict['Zurich, Switzerland']['lon'],geoDict[currentCity]['lon']],
                             lat = [geoDict[homeCity]['lat'],geoDict['Zurich, Switzerland']['lat'],geoDict[currentCity]['lat']],
                             mode = 'markers+lines', 
                             geo = 'geo',
                             #text = texts[i], 
                             #textposition = textlocs[i],
                             #textfont = dict(size = 18, color = 'black'),
                             marker = dict(size=8, opacity = 1, line=dict(color='black',width = 1))
                            )
            userGroups.append(userGroup.copy())
            userGroup['geo'] = 'geo2'
            userGroups.append(userGroup)
    

    layout = go.Layout(
            #title = 'Current Towns',
        showlegend = False,
        #autosize=True,
        #width = 1000,
        margin=go.Margin(
            l=0,
            r=30,
            b=0,
            t=30
        ),
    geo = dict(
            scope='world',
            showland = True,
            landcolor='white',
            showcountries = True,
            showcoastlines=True,
            domain = dict(x = [0,.6],
                          y = [0,1]),
            lonaxis = dict(range = [-115,180]),
            lataxis = dict(range = [-55,70])
        ),
    geo2 = dict(scope = 'europe',
                resolution = 50,
                showland = True,
                landcolor = 'white',
                showcountries = True,
                showcoastlines = True,
                domain = dict(x = [0.65, 1],
                              y = [0, 1]),
                lonaxis = dict(range = [-10,25]),
                lataxis = dict(range = [37.5,60]))
                )

    
    myUsers = dict(data=baseMap+userGroups,
                   layout = layout)
    
    
    py.offline.plot(myUsers)
    
def timePlot(df):
    # find the earliest time
    bigBang = df[['Start Master','Start PhD','Start Position']].min().min()
    
    allNations,_,_ = countNations(df)
    allNations = list(allNations)
    
    myTimes = pd.date_range(bigBang,dt.datetime(2017,12,31),freq='3MS')
    overTheYears = {key: dict(x=[],y=[]) for key in allNations}
    for time in myTimes:
        # find all nations present at the time
        presentdf = df.loc[(df['Start PhD'] <= time) & (df['End PhD'] >= time) |
        (df['Start Master'] <= time) & (df['End Master'] >= time) |
        (df['Start Position'] <= time) & (df['End Position'] >= time)]
        
        presentNations,_,natCount = countNations(presentdf,normalize=True)
        locTot = 0.
        for nation in allNations:
            if nation in presentNations:
                locTot = locTot+natCount[nation]*100
                overTheYears[nation]['y'].append(locTot)
            else:
                overTheYears[nation]['y'].append(locTot)
                
    # now build the traces
    traces = []
    for nation in allNations:
        traces.append(go.Scatter(
                x = myTimes,
                y = overTheYears[nation]['y'],
                fill='tonexty',
                name=nation,
                mode = 'lines'))
        
    py.offline.plot(traces)
    
    return overTheYears

def scopusCrawl(dftot):
    marco = ScopusAuthor(7005206227)
    coauthors = marco.get_coauthors()
    scopusdf = pd.DataFrame({'Name':[a.name for a in coauthors],'ID':[a.scopus_id for a in coauthors]})
    scopusdf['Last Name'] = ''
    for _,row in scopusdf.iterrows():
        name = row['Name'].split()
        row['Last Name'] = name[-1]
    
    for _,row in mydf_tot.iterrows():
        name = row['Name'].split()
        lastName = name[-1]
        row['ScopusID'] = scopusdf[scopusdf['Last Name'].str.contains(lastName)]['ID'].to_string(index=False)
    
    # find all authors
    dftot.replace('Series([], )',np.nan,inplace=True)
    
    # some errors in scopus and due to name changes we have to add some by hand:
    dftot.loc[dftot['Name'] == 'Galatea Paredes Menendez','ScopusID'] = '9532374000'
    dftot.loc[dftot['Name'] == 'Alba Zappone','ScopusID'] = '6602658137'
    dftot.loc[dftot['Name'] == 'Ashwin Kumar Rajagopalan','ScopusID'] = '57045641800'
    dftot.loc[dftot['Name'] == 'Janik Schneeberger','ScopusID'] = '57195526213'
    dftot.loc[dftot['Name'] == 'Markus Huber','ScopusID'] = '55658056495'
    dftot.loc[dftot['Name'] == 'Mischa Repmann','ScopusID'] = '35097004100'
    
    myAuthors = dftot[dftot['ScopusID'].notnull()]
    
    #adjacency matrix
    adjac = pd.DataFrame(columns=myAuthors['Name'],index=myAuthors['Name'])
    
    for com in itertools.combinations_with_replacement(myAuthors['Name'],2):
        aud1 = myAuthors[myAuthors['Name'] == com[0]]['ScopusID'].to_string(index=False)
        aud2 = myAuthors[myAuthors['Name'] == com[1]]['ScopusID'].to_string(index=False)
        print('Checking collabos between '+com[0]+' and '+com[1]+'...')
#        print(aud1)
#        print(aud2)
        s = ScopusSearch('AU-ID ('+str(aud1)+' AND '+str(aud2)+')')
#        print(len(s.EIDS))
        print(adjac[com[0]][com[1]])
        adjac.loc[com[1],com[0]] = len(s.EIDS)
        print(adjac[com[0]][com[1]])
    
if __name__ == '__main__':
    main()