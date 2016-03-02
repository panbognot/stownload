# -*- coding: utf-8 -*-
"""
Created on Wed Mar 02 17:30:18 2016

@author: PradoArturo
"""

from bs4 import BeautifulSoup
import urllib2
import string

url = 'http://www.pesobility.com/stock'

#trick the server of pesobility to think that you are accessing through
#   the use of a web browser
req = urllib2.Request(url, headers={'User-Agent' : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30"}) 
con = urllib2.urlopen(req)

#copy the html text downloaded from the server
html_text = con.read()

#parse the html using beautiful soup library
soup = BeautifulSoup(html_text, 'html.parser')

#Get the list of companies
companyList = soup.find_all('tr')

#Process all companies
for link in companyList:
    company = link.td.a.text
    
    price = link.contents[5]
    priceTextEnd = string.find(price.text, ' ')
    priceText = (price.text)[:priceTextEnd]
    print "%s Price: %s" % (company, priceText)

pass