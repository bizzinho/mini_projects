# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:34:21 2020

@author: Dave
"""

import imaplib
import email
from email import policy
from bs4 import BeautifulSoup
# import requests
import time
from selenium import webdriver
import pandas as pd
import os


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
allNewListings = []
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
            
            newListings = [casa.split('adId=')[1].split('&lang')[0] for casa in caseNuove]
            allNewListings.extend(newListings)
    nMails += 1
    if nMails > 2:
        break

allNewListings = list(set(allNewListings))
print("-----")
print("{} unique new listings total.".format(len(allNewListings)))

# get the page of each new listing
driver = webdriver.Chrome()
for listing in allNewListings:
    listing_address = 'https://www.idealista.pt/imovel/'+listing+'/'
    driver.get(listing_address)
    # XX check that page was loaded correctly and we are not blocked    
    page = driver.page_source
    with open('./pages_html/'+listing+pd.Timestamp.now().strftime('%d%b%Y')+'.html','w+',encoding="utf-8") as f:
        f.write(page)
    time.sleep(10) # we are benign and don't want to stress the servers

# add new listings in DB
df = pd.read_excel('Apartment_PT.xlsx',index_col = 0
                   sheet_name = 'DB')

df_new = pd.DataFrame(columns = df.columns)
df_new.index.name = df.index.name
# go over all new html files that haven't been read out yet (are not in folder 'done')
for fname in [file for file in os.listdir('./pages_html/') if (file!='done') and (file.endswith('.html'))]:
    # read file in
    with open('./pages_html/'+fname,'r',encoding="utf-8") as f:
        page = f.read()
    soup = BeautifulSoup(page)
    
    # remember ID
    ID = 'IDEALISTA_'+fname[:-15]
    
    # find price
    price = float(soup.find('span',attrs = {'class':'info-data-price'}).text.replace('€',''))
    
    # size 
    size = float(soup.find('div',attrs = {'class':'info-features'}).text.split('m² construídos')[0])
    
    # bedrooms
    for info in soup.find('div',attrs = {'class':'info-features'}).find_all('span')[::-1]:
        if (len(info.text) == 2) and (info.text.startswith('T')):
            bedrooms = int(info.text[1])
            break
    
    # date found (is in the filename)
    dateFound = pd.to_datetime(fname[-14:-5])
    
    # link (can be created knowing the ID)
    link = 'https://www.idealista.pt/imovel/'+fname[:-15]+'/'
    
    # remaining entries: 
    # Beach, Type, Size (Uteis), Lote, Bathrooms, Year Built, Garage, Floor, Elevator, Energy Certificate, AC, Solar Panels, Piscina, Veranda, Terrace, Built-in Closets, Seaview, Riaview, Beach Distance, Ria Distance, Orientation

    
