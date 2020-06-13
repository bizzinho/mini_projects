# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 18:42:03 2019

@author: Dave
"""
from PIL import Image # to read image metadata
import os, dateutil, itertools
from shutil import copy2
import numpy as np
# to send email
#from oauth2client import file, client, tools
from googleapiclient.discovery import build
#from httplib2 import Http
import base64
from email.mime.text import MIMEText
import pickle
import time


baseFolder = '/volume1/photo/PhonePix/'

emFolder_Ana = baseFolder+'Emily/'  # location of Ana's pix
emFolder_Dave = baseFolder+'Emi/'  # location of Dave's pix
#
emFolder_photoStation = baseFolder+'Emily_shared/' # photostation folder
unsureFolder = baseFolder+'z_unsure/' # unsure folder

unsure = []

pix_Ana = [] # pix by Ana, candidates for being moved into shared folder
pix_Dave = [] # pix by Dave, candidates for being moved into shared folder

pix_photostation = []

Ana = (emFolder_Ana, pix_Ana)
Dave = (emFolder_Dave, pix_Dave)
PS = (emFolder_photoStation, pix_photostation)

myAll = (Ana, Dave, PS)

for folder, pixList in myAll:
    for f in os.listdir(folder):
        if (f[-4:] == '.jpg') or (f[-5:] == '.jpeg'): # check if is jpeg image
            myName = folder+f
#            myExt = str.split(f,'.')[-1]
#            if '-WA' in f: # this picture was sent via whatsapp and has a suffix that we want to remove when comparing
#                myNickname = str.strip(str.split(f,'-WA')[0])+'.'+myExt
#            else:
#                myNickname = myName
                
            fileSize = os.path.getsize(myName)
            # metadata
            img = Image.open(myName)
            try:
                timeTaken = dateutil.parser.parse(img._getexif()[36867])
            except:
                timeTaken = None
                
#            try:
#                uID = img._getexif()[42016] # should be unique ID, but doesn't look very unique to me
#            except:
#                uID = None
            
            img.close()
            
            pixList.append((myName, f, fileSize, timeTaken))
            
candidates = pix_Ana + pix_Dave

# remove pix that are already in destination folder
pix_photostation_short = [x[1:] for x in pix_photostation] # don't care about full path
candidates = [c for c in candidates if c[1:] not in pix_photostation_short]      
            
# find files with exactly the same filesize (super suspicious)
fileSizeList = [elem[2] for elem in candidates]
duplicateFilesizes = list(set([size for size in fileSizeList if fileSizeList.count(size) > 1]))

possibleTwins_size = []
for filesize in duplicateFilesizes:
    possibleTwins_size.append( tuple([elem for elem in pix_Ana if elem[2] == filesize] + [elem for elem in pix_Dave if elem[2] == filesize]))

for twins in possibleTwins_size:
    # if datetime is the same, consider them twins and keep one
    
    times = [elem[3] for elem in twins]
    if None not in times:
        # all times are there
        if len(set(times)) == 1:
            # remove all twins except the first
            for twin in twins[1:]:
                candidates.remove(twin)
    else:
        # at least one datetime is missing, we need to make a diff
        remItem = []
        twinCombs = list(itertools.combinations(twins,2))
        for comb in twinCombs:
            img1 = Image.open(comb[0][0])
            img2 = Image.open(comb[1][0])
            
            if img1.size == img2.size:
                diff = np.linalg.norm(np.array(img1) - np.array(img2))
                if diff == 0:
                    remItem.append(comb[1])
                
            img1.close()
            img2.close()
            
        for twin in set(remItem):
            candidates.remove(twin)
            
datetimeList = [elem[3] for elem in candidates]
duplicateDatetimes = list(set([time for time in datetimeList if datetimeList.count(time) > 1]))

duplicateDatetimes.remove(None)

possibleTwins_time = []
for datetime in duplicateDatetimes:
    possibleTwins_time.append( tuple([elem for elem in pix_Ana if elem[3] == datetime] + [elem for elem in pix_Dave if elem[3] == datetime]))
    
for twins in possibleTwins_time:
    remItem = []
    twinCombs = list(itertools.combinations(twins,2))
    for comb in twinCombs:
        img1 = Image.open(comb[0][0])
        img2 = Image.open(comb[1][0])
        
#        if img1.size[1] / img1.size[0] == img2.size[1] / img2.size[0]:
            # the two images have the same ratio
        if (comb[0][2] > comb[1][2]) and ('-WA' in comb[1][0]):
            remItem.append(comb[1])
        elif (comb[1][2] > comb[0][2]) and ('-WA' in comb[0][0]):
            remItem.append(comb[0])
        else:
            # the pix have the same ratios but none seems to be coming from whatsapp
            if comb[0][2] > comb[1][2]:
                unsure.append(comb[1])
                remItem.append(comb[1]) # remove it for now, but copy it in a sep folder to check
            else:
                unsure.append(comb[0])
                remItem.append(comb[0])
        
        img1.close()
        img2.close()
            
    for twin in set(remItem):
            candidates.remove(twin)
                 

for pic in candidates:
    copy2(pic[0], emFolder_photoStation)
    
for uns in unsure:
    copy2(uns[0], unsureFolder)
    
if 'pic_list.txt' in os.listdir(baseFolder):
    with open(baseFolder+'pic_list.txt', 'r') as f:
        oldList =f.readlines()
    oldList = [l.rstrip('\n') for l in oldList]
else:
    oldList = []    


newList = [item[1] for item in pix_photostation+candidates]
with open(baseFolder+'pic_list.txt', 'w') as f:
    for item in newList:
        f.write("%s\n" % item)
            
n_newPix = len(newList) - len(oldList)

try:
    for file in [emFolder_photoStation+f for f in newList]:
        os.system("synoindex -a {}".format(file))
except:
    print("Not on a synology server")

if n_newPix > 0:        
# send mail alert if new, maybe attach a pic
    with open(baseFolder+'token.pickle','rb') as pickle_cred:
        cred = pickle.load(pickle_cred)
    
    
    GMAIL = build('gmail', 'v1', credentials=cred)
    
    recipients =  ['dave.ochsenbein@gmail.com', 'ana.grangeia@outlook.com', 'ochsenbein-veglio@gmx.ch' ,'amsgrangeia@gmail.com', 'deisygrangeia@gmail.com', 'ericagrangeia@gmail.com', 'ott.floriandimitri@gmail.com']
    
    for recipient in recipients:
        n_tries = 1
        mailSent = False
        while (n_tries <= 5) and (mailSent == False):
        
            try:
                message = MIMEText(u'Hey/Olá/Hoi/Ciao fans of Emily!<br><br>There are {} new pictures of Emily! Go have a look <a href="https://SchmexyServer.fr.quickconnect.to/photo/share/AJSOOf1W">here</a>!<br><br>Ana & Dave'.format(n_newPix),'html')
                message['to'] = recipient
                message['subject'] = '{} new pictures of Emily :)'.format(n_newPix)
                msg = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
                
                message = (GMAIL.users().messages().send(userId='me', body=msg)
                               .execute())
                mailSent = True
            except:
                n_tries += 1
                time.sleep(60)
