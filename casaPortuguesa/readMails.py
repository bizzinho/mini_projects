# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:34:21 2020

@author: Dave
"""

import imaplib
import email
from email import policy
from bs4 import BeautifulSoup
import pandas as pd
import os
import warnings

with open('lastDateChecked.txt','r') as f:
    lastDateChecked = pd.to_datetime(f.read())

emailaddy = 'anadaveawesome@gmail.com'
with open('appPWD.txt','r') as f:
    pwd = f.read()
smtpServer = 'imap.gmail.com'
smtpPort = 993

mail = imaplib.IMAP4_SSL(smtpServer)
mail.login(emailaddy, pwd)

mail.select('inbox')

_, data = mail.search(None, '(OR FROM "noreply@idealista.pt" FROM "noresponder.avisos@idealista.pt" SINCE "{}")'.format(lastDateChecked.strftime('%d-%b-%Y')))
mail_ids = data[0]

id_list = mail_ids.split()

nMails = 0
allNewListings = []
for myID in id_list:
    typ, data = mail.fetch(myID.decode("utf-8") , '(RFC822)' )

    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1], policy=policy.default)
            email_subject = msg['subject']
            email_from = msg['from']
            email_date = msg['Date']
            print('From : ' + email_from + '\n')
            print('Subject : ' + email_subject + '\n')
            print('Date : ' + email_date + '\n')
            
            body = msg.get_payload()[0].get_payload()[0].get_payload(decode = True)
            soup = BeautifulSoup(body, features="html.parser")
            links = soup.find_all('a')
            caseNuove = [link['href'] for link in links if (link.get_text() != '') and 
                         ('anadaveawesome' not in link.get_text()) and
                         (link.get_text() != 'As tuas pesquisas') and 
                         (link.get_text() != 'Contactar') and 
                         ('Ver todos os' not in link.get_text()) and 
                         ('Cancelar' not in link.get_text()) and 
                         (link.get_text() != 'Faz download da app do idealista') and not 
                         (('Ver' in link.get_text()) and ('fotos' in link.get_text()))]
            print("New listings in this mail: {}".format(len(caseNuove)))
            try:
                newListings = [casa.split('adId=')[1].split('&lang')[0] for casa in caseNuove]
            except:
                newListings = [casa.split('www.idealista.pt/imovel/')[1].split('/')[0] for casa in caseNuove]
            allNewListings.extend(newListings)
    nMails += 1

allNewListings = list(set(allNewListings))
print("-----")
print("Number of new listings found: {}".format(len(allNewListings)))

with open('lastDateChecked.txt','w+') as f:
    f.write(pd.Timestamp.now().isoformat())

try:
    with open('backlog.txt','r') as f:
        existingListings = f.read().split()
except:
    warnings.warn("Could not find a backlog.")

print("Size of existing backlog: {}".format(len(existingListings)))

newBacklog = list(set(existingListings + allNewListings))

print("Total size of backlog: {}".format(len(newBacklog)))

with open('backlog.txt','w+') as f:
    f.write("\n".join(sorted(newBacklog)))