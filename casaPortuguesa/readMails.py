# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:34:21 2020

@author: Dave
"""

import imaplib
import email
from email import policy
from bs4 import BeautifulSoup

emailaddy = 'anadaveawesome@gmail.com'
with open('appPWD.txt','r') as f:
    pwd = f.read()
smtpServer = 'imap.gmail.com'
smtpPort = 993

mail = imaplib.IMAP4_SSL(smtpServer)
mail.login(emailaddy, pwd)

mail.select('inbox')

_, data = mail.search(None, "FROM 'noreply@idealista.pt'")
mail_ids = data[0]

id_list = mail_ids.split()   
first_email_id = int(id_list[0])
latest_email_id = int(id_list[-1])

nMails = 0
allNewListings = {}
for i in range(latest_email_id,first_email_id, -1):
    typ, data = mail.fetch(str(i), '(RFC822)' )

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
                         (link.get_text() != 'As tuas pesquisas') and 
                         (link.get_text() != 'Contactar') and 
                         ('Ver todos os anúncios de Casas' not in link.get_text()) and 
                         (link.get_text() != 'Cancelar a subscrição') and 
                         (link.get_text() != 'Faz download da app do idealista') and not 
                         (('Ver' in link.get_text()) and ('fotos' in link.get_text()))]
            print("New listings in this mail: {}".format(len(caseNuove)))
            
            newListings = {casa.split('adId=')[1].split('&lang')[0]:casa for casa in caseNuove}
            allNewListings.update(newListings)
    nMails += 1
    if nMails > 2:
        break

allNewListings = list(set(allNewListings))
print("{} unique new listings total.".format(len(allNewListings)))