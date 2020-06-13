# -*- coding: utf-8 -*-
"""
Created on Sat May 16 16:32:06 2020

@author: Dave
"""
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import time

with open('backlog.txt','r') as f:
    backlog = f.read().split()

toBeRemoved = []
# get the page of each new listing
driver = webdriver.Chrome()
for listing in backlog:
    print("Listing: {}".format(listing))
    listing_address = 'https://www.idealista.pt/imovel/'+listing+'/'
    driver.get(listing_address)
    # XX check that page was loaded correctly and we are not blocked    
    page = driver.page_source
    soup = BeautifulSoup(page,features="html.parser")
    if 'Foram detectadas várias solicitações tuas em pouco tempo.' not in soup.text:
        if (soup.find('div',{'class':'feedback warning icon-feedbk-alert'}) is not None) and ('Lamentamos' in soup.find('div',{'class':'feedback warning icon-feedbk-alert'}).text):
            print("FAIL: Listing was not on idealista anymore. Will remove it from the backlog.".format(listing))
            toBeRemoved.append(listing)
        else:
            with open('./pages_html/'+listing+'_'+pd.Timestamp.now().strftime('%d%b%Y')+'.html','w+',encoding="utf-8") as f:
                f.write(page)
                toBeRemoved.append(listing)
                print("SUCCESS: Listing was saved locally.".format(listing))
        time.sleep(10) # we are benign and don't want to stress the servers
    else:
        print("DAMN, THE PO-PO CAUGHT US! RUN FOR IT!!!")
        break # we got caught. Let's take a break
    
newBacklog = sorted(list(set(backlog) - set(toBeRemoved)))

if len(newBacklog) == 0:
    print("All listings in the backlog were saved locally!")
else:
    print('There are {} listings remaining in the backlog. Solve the captcha or try at a later date.'.format(len(newBacklog)))

with open('backlog.txt','w+') as f:
    f.write("\n".join(sorted(newBacklog)))