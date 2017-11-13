#from __future__ import print_function
import httplib2
import os
import pandas as pd
import numpy as np
import datetime as dt
import networkx as nx
import pdb
import itertools

import plotly as py
import plotly.figure_factory as ff
import plotly.graph_objs as go

import matplotlib as mpl
import matplotlib.cm as cm

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
from scopus import ScopusAbstract

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
    rangeName = 'Sheet1!A2:N83'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    
    df = pd.DataFrame(values[1:],columns=values[0])
    df.drop(["Completeness Check"],axis=1,inplace=True)
    
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
    
    for i in range(5,11):
        #print(i)
        df.iloc[:,i] = pd.to_datetime(df.iloc[:,i])
    
    df['Home Town'] = df['Home Town'].str.split(';')    
    df['Current Town'] = df['Current Town'].str.split(';')
    
    df['Topic PhD / PostDoc (at SPL)'] = df['Topic PhD / PostDoc (at SPL)'].str.split(',')
    df = df.set_index('Name',drop=False)

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
    
def plotGraph(A2 = None,removeMarco = False):
    
    if A2 is None:
        A2 = pd.read_excel('collaborators_scopus.csv')
        A = A2.as_matrix()[:,1:]
    else:
        A = A2.as_matrix()
        myFullNames = list(A2.columns)
    
    # simplify names
    myNames = [name.split()[0] if name.split()[0] not in ['Shigeharu','Matthäus','Stefan','Matteo','Markus','Christian','Giovanni','Subrahmaniam','José'] else 
               'John' if name.split()[0] == 'Giovanni' else 
               'Thes' if name.split()[0] == 'Matthäus' else 
               'Hari' if name.split()[0] == 'Subrahmaniam' else 
               'Paco' if name.split()[0] == 'José' else 
               'Shige' if name.split()[0] == 'Shigeharu' else 
               'Matteo S.' if name.split()[-1] == 'Salvalaglio' else 
               'Matteo G.' if name.split()[-1] == 'Gazzani' else 
               name.split()[-1] for name in list(myFullNames)]
    
    A = np.nan_to_num(np.matrix(A).astype(float))
    
    G = nx.from_numpy_matrix(A)
    if removeMarco == True:
        G.remove_node(0)
#        myNames = myNames[1:]
        
        
    
    #pos = nx.get_node_attributes(G,'pos')
    
    # remove all self-loops
    for i in range(1,len(myNames)):
        G.remove_edge(i,i)
    
#    for isolated_node in nx.isolates(G):
#        myNames.pop(isolated_node)
    G.remove_nodes_from(nx.isolates(G)) 
    
    pos = nx.spring_layout(G,dim=2,k=1/np.sqrt(G.number_of_nodes()),iterations = 200)
#    pos = nx.circular_layout(G)
        
    edgeWeights = [d['weight'] for (_,_,d) in G.edges(data=True)]
    maxEdgeW = np.max(edgeWeights)

    
#    norm = mpl.colors.Normalize(vmin=0, vmax=maxEdgeW)
#    m = cm.ScalarMappable(cmap=cm.seismic,norm=norm)
    cmap = cm.copper

    edge_trace = []
    for edge in G.edges(data=True):
        strength = edge[2]['weight']/maxEdgeW
        edge_trace.append(
                go.Scatter(
                    x=[pos[edge[0]][0],pos[edge[1]][0]],
                    y=[pos[edge[0]][1],pos[edge[1]][1]],
                    line=dict(color='rgb({},{},{})'.format(*np.array(cmap(strength)[0:3])*255),
                              width=strength*7),
                    hoverinfo='none',
                    mode='lines')
                )
    
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        textposition='bottom',
        hoverinfo='text',
        text = [],
        marker=go.Marker(
            showscale=True,
            # colorscale options
            # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
            # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
            colorscale='copper',
            reversescale=False,
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
        node_trace['text'].append(myNames[node])
        
    for node, adjacencies in enumerate(G.adjacency_list()):
        if node > 0:
            node_trace['marker']['color'].append(len(adjacencies))
#            node_info = '# of connections: '+str(len(adjacencies))
        else:
            node_trace['marker']['color'].append(0)
#            node_info = '# of connections: '+str(len(adjacencies))
#            node_trace['text'].append(node_info)
        

    fig = go.Figure(data=go.Data(edge_trace+[node_trace]),
         layout=go.Layout(
            title='SPL Authorship Network',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=go.XAxis(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=go.YAxis(showgrid=False, zeroline=False, showticklabels=False)))

    py.offline.plot(fig)
    
    return G
    
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
        allHomes = df['Home Town'].dropna().tolist()
        allCurrents = df['Current Town'].dropna().tolist()
        allTowns = [town for sublist in allHomes for town in sublist]
        allTowns.extend([town for sublist in allCurrents for town in sublist])
        
        geoDict = {}
        for town in np.unique(allTowns):
            print(town)
            myloc = geolocator.geocode(town,timeout=20)
            geoDict[town] =  dict(lon=myloc.longitude,lat = myloc.latitude)
    
    userGroups = []
    for _,homeCity,currentCity in df[['Home Town','Current Town']].itertuples():
        if homeCity is not np.nan:
            for city in currentCity:
                userGroup = dict(type='scattergeo',
                                 lon = [geoDict[homeCity[0]]['lon'],geoDict['Zurich, Switzerland']['lon'],geoDict[city]['lon']],
                                 lat = [geoDict[homeCity[0]]['lat'],geoDict['Zurich, Switzerland']['lat'],geoDict[city]['lat']],
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
    
    # preparations for the topics
    allTopics = set([str.strip(topic) for _,topics in df['Topic PhD / PostDoc (at SPL)'].iteritems() if topics is not np.nan for topic in topics ])
    
    
    myTimes = pd.date_range(bigBang,dt.datetime(2017,12,31),freq='3MS')
    overTheYears = {key: dict(x=[],y=[],text=[]) for key in allNations+list(allTopics)}
    overTheYears['M'] = []
    overTheYears['F'] = []
    overTheYears['gendertext'] = []
    
    overTheYears['duration'] = dict(x=[],y=[])
    overTheYears['durationMean'] = []
    overTheYears['durationtext'] = []
    
    
    PhDEnders = []
    
    for time in myTimes.union([dt.datetime(2017,12,15)]):
        # find all nations present at the time
        presentdf = df.loc[(df['Start PhD'] <= time) & (df['End PhD'] >= time) |
        (df['Start Master'] <= time) & (df['End Master'] >= time) |
        (df['Start Position'] <= time) & (df['End Position'] >= time)]
        
        
        # find all phds that have ended in the last time step
        newFinishers = df[(abs((time - df['End PhD'])) < dt.timedelta(93)) & (time > df['End PhD'])]['Name'].tolist()
        PhDEnders.extend(
                newFinishers
                )
        
        
        for finisher in newFinishers:
            try:
                overTheYears['duration']['y'].extend(((df.loc[finisher,'End PhD']-df.loc[finisher,'Start PhD'])[df.loc[finisher,'Start PhD'].notnull()].dt.days / 365.25).tolist())
            except:
                overTheYears['duration']['y'].append(((df.loc[finisher,'End PhD']-df.loc[finisher,'Start PhD']).days / 365.25))
            overTheYears['duration']['x'].append(df.loc[finisher,'End PhD'])


        if len(PhDEnders) > 0:
            overTheYears['durationMean'].append((df.loc[PhDEnders[-5:],'End PhD']-df.loc[PhDEnders[-5:],'Start PhD']).mean().days / 365.25)
        else:
            overTheYears['durationMean'].append(0)
        
        # nationalities
        presentNations,_,natCount = countNations(presentdf,normalize=False)
        locTot = 0.
        for nation in allNations:
            if nation in presentNations:
                locTot = locTot+natCount[nation]
                overTheYears[nation]['y'].append(locTot)
                overTheYears[nation]['text'].append(str(natCount[nation]))
#                print(overTheYears[nation]['text'])
            else:
                overTheYears[nation]['y'].append(locTot)
                overTheYears[nation]['text'].append('0')
                
        # genders
        genders = presentdf['Gender'].value_counts()
        overTheYears['M'].append(100)
        maleFraction = genders.M / presentdf['Gender'].count() * 100
        overTheYears['gendertext'].append('{:3.1f}% girls, {:3.1f}% boys'.format(100-maleFraction,maleFraction))
        if np.any(presentdf['Gender'].isin(['F'])):
            overTheYears['F'].append(genders.F / presentdf['Gender'].count()*100)
        else:
            overTheYears['F'].append(0)
            
        # topics
        presentTopics = [str.strip(topic) for _,topics in presentdf['Topic PhD / PostDoc (at SPL)'].iteritems() if topics is not np.nan for topic in topics ]
        countTopics = Counter(presentTopics)
        locTot = 0
        for topic in allTopics:
            
            if (topic in presentTopics) and (len(presentTopics)>0):
                locTot = locTot + countTopics[topic] / len(presentTopics)*100
                overTheYears[topic]['y'].append(locTot) 
                overTheYears[topic]['text'].append('{:d}%'.format(int(countTopics[topic] / len(presentTopics)*100)))
            else:
                overTheYears[topic]['y'].append(locTot)
                overTheYears[topic]['text'].append('0%') 
                
    # now build the traces
    traces = []
    
    for nation in allNations:
        traces.append(go.Scatter(
                x = myTimes,
                y = overTheYears[nation]['y'],
                text= overTheYears[nation]['text'],
                fill='tonexty',
                name=nation,
                hoverinfo='x+name+text',
                mode = 'lines'))
        
    layout = go.Layout(xaxis=dict(range=[dt.datetime(1997,5,1),dt.datetime(2017,12,31)]))
    
    fig = go.Figure(data=traces,layout=layout)
    
    py.offline.plot(fig,show_link = False,filename='nationalities.html')
    
    genderTrace = [go.Scatter(x = myTimes,
                y = overTheYears['F'],
                text = overTheYears['gendertext'],
                hoverinfo='text',
                fill='tonexty',
                name='Ladies',
                mode = 'lines'),
            go.Scatter(x = myTimes,
                y = overTheYears['M'],
                text = overTheYears['gendertext'],
                hoverinfo='text',
                fill='tonexty',
                name='Gentlemen',
                mode = 'lines')]
            
    fig2 = go.Figure(data=genderTrace,layout=layout)
    py.offline.plot(fig2,show_link = False,filename='genders.html')
    
    topicTrace = []
    for topic in allTopics:
        topicTrace.append(go.Scatter(
                x = myTimes,
                y = overTheYears[topic]['y'],
                text= overTheYears[topic]['text'],
                fill='tonexty',
                name=topic,
                hoverinfo='x+name+text',
                mode = 'lines'))
        
    
    fig3 = go.Figure(data=topicTrace,layout=layout)
    
    py.offline.plot(fig3,show_link = False,filename='topics.html')
    
    durationTrace = [go.Scatter(x = myTimes,
                y = overTheYears['durationMean'],
                text = overTheYears['durationtext'],
                hoverinfo='text',
                name='Duration',
                mode = 'lines'),
            go.Scatter(x = overTheYears['duration']['x'],
                y = overTheYears['duration']['y'],
                text = overTheYears['durationtext'],
                hoverinfo='text',
                name='Duration',
                mode = 'markers'),]
            
    fig4 = go.Figure(data=durationTrace,layout=layout)
    py.offline.plot(fig4,show_link = False,filename='duration.html')
    
    return overTheYears

def scopusCrawl(mydf_tot,myCollabos = None):
    
    dftot = mydf_tot.drop_duplicates(subset='Name',keep='last').copy() # because of people that have multiple positions
    
    marco = ScopusAuthor(7005206227)
    coauthors = marco.get_coauthors()
    scopusdf = pd.DataFrame({'Name':[a.name for a in coauthors],'ID':[a.scopus_id for a in coauthors]})
    scopusdf['Last Name'] = ''
    for _,row in scopusdf.iterrows():
        name = row['Name'].split()
        row['Last Name'] = name[-1]
    
    for index,row in dftot.iterrows():
        name = row['Name'].split()
        lastName = name[-1]
        myID = scopusdf[scopusdf['Last Name'].str.contains(lastName)]['ID'].to_string(index=False)
        dftot.loc[index,'ScopusID'] = myID
    # find all authors
    dftot.replace('Series([], )',np.nan,inplace=True)
    
    # there are some bugs in scopus and due to name changes we have to add some by hand:
    dftot.loc[dftot['Name'] == 'Galatea Paredes Menendez','ScopusID'] = '9532374000'
    dftot.loc[dftot['Name'] == 'Alba Zappone','ScopusID'] = '6602658137'
    dftot.loc[dftot['Name'] == 'Ashwin Kumar Rajagopalan','ScopusID'] = '57045641800'
    dftot.loc[dftot['Name'] == 'Janik Schneeberger','ScopusID'] = '57195526213'
    dftot.loc[dftot['Name'] == 'Markus Huber','ScopusID'] = '55658056495'
    dftot.loc[dftot['Name'] == 'Mischa Repmann','ScopusID'] = '35097004100'
    dftot.loc[dftot['Name'] == 'Werner Dörfler','ScopusID'] = '6701683560'
    dftot.loc[dftot['Name'] == 'Detlef Röderer','ScopusID'] = '55227680000'
    
    myAuthors = dftot[dftot['ScopusID'].notnull()]
    
    adjac = pd.DataFrame(columns=myAuthors['Name'],index=myAuthors['Name'])
    adjac.replace(np.nan,0,inplace=True)
#    return myAuthors
    checkedPapers = []
    myCollaboPapers = []
    myCollabos = []
    for author in myAuthors['ScopusID']:
        authorName = myAuthors[myAuthors['ScopusID']==author]['Name']
        print(authorName)
        scopusAuthor = ScopusAuthor(author)
        papers = scopusAuthor.get_document_eids()
        adjac.loc[authorName,authorName] = len(papers)
        for paper in papers:
            if paper not in checkedPapers:
                checkedPapers.append(paper)
                paperAuthors = ScopusAbstract(paper).authors
                paperAuthors_IDs = [paperAuthor.auid for paperAuthor in paperAuthors]
                allAuthorsString = '|'.join(paperAuthors_IDs)
                if myAuthors['ScopusID'].str.contains(allAuthorsString).sum() > 1:
                    myCollabos.append(myAuthors[myAuthors['ScopusID'].str.contains(allAuthorsString)]['Name'].tolist())    
                    myCollaboPapers.append(paper)
                
    # some special combos
    myCollabos.extend([['Dave Ochsenbein','Marco Mazzotti'], # nano letters paper
                      ['Dave Ochsenbein','Thomas Vetter', 'Marco Mazzotti'], # modeling book chapter
                      ['Dave Ochsenbein','Thomas Vetter','Marco Mazzotti','Giovanni Maria Maggioni','Christian Lindenberg'], 
                      ['Marco Mazzotti','Marco Mazzotti'],# 1991 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'], # 1993 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1995 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1995 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1995 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1995 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1996 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1996 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1997 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 1998 book chapter
                      ['Marco Mazzotti','Cristiano Migliorini'],# 1998 book chapter
                      ['Marco Mazzotti','Orazio Di Giovanni'],# 1998 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2001 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2002 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2002 book chapter
                      ['Marco Mazzotti','Stefanie Abel'],# 2002 book chapter
                      ['Marco Mazzotti','Orazio Di Giovanni', 'Arvind Rajendran','Werner Dörfler'],# 2002 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2003 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2003 book chapter
                      ['Marco Mazzotti','Stefanie Abel'],# 2003 book chapter
                      ['Marco Mazzotti','Arvind Rajendran'],# 2003 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2005 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2005 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2005 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2005 book chapter
                      ['Marco Mazzotti','Marco Mazzotti'],# 2007 book chapter
                      ['Marco Mazzotti','Marco Mazzotti']])# 2008 book chapter
    

    for i in range(2,7):
        killercombos = [tuple(collabo) for collabo in myCollabos if len(collabo)==i]
        comboCounter = Counter(killercombos)
        
        print('{} collaborators'.format(i))
        print(comboCounter.most_common(3))
    
    for collabo in myCollabos:
        for duo in itertools.combinations(sorted(collabo),2):
            if 'Marco Mazzotti' in duo:
                adjac.loc[duo[not duo.index('Marco Mazzotti')],'Marco Mazzotti'] += 1
            else:
                adjac.loc[duo[1],duo[0]] += 1
            
    return adjac
            
    
    #adjacency matrix
#    adjac = pd.DataFrame(columns=myAuthors['Name'],index=myAuthors['Name'])
#    
#    collabo_duos = set()
#    for com in itertools.combinations_with_replacement(myAuthors['Name'],2):
#        aud1 = myAuthors[myAuthors['Name'] == com[0]]['ScopusID'].to_string(index=False)
#        aud2 = myAuthors[myAuthors['Name'] == com[1]]['ScopusID'].to_string(index=False)
#        print('Checking collabos between '+com[0]+' and '+com[1]+'...')
##        print(aud1)
##        print(aud2)
#        s = ScopusSearch('AU-ID ('+str(aud1)+' AND '+str(aud2)+')')
##        print(len(s.EIDS))
#        adjac.loc[com[1],com[0]] = len(s.EIDS)
#        if (len(s.EIDS)>1) and ('Marco Mazzotti' not in com) and (com[0] is not com[1]):
#            collabo_duos.update(com)
#            
#    return adjac, collabo_duos
    
 
    
if __name__ == '__main__':
    main()