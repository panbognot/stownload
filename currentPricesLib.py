# -*- coding: utf-8 -*-
"""
Created on Wed Mar 02 17:30:18 2016

@author: PradoArturo
"""

from bs4 import BeautifulSoup
import urllib2
import string
import time
import datetime
from datetime import timedelta as td
from datetime import datetime as dt
import queryStockDb as qs
import pandas as pd
import numpy as np
import requests

#download the current prices of stocks
def downloadCurrentPricesData():
    curTimestamp = time.strftime("%Y-%m-%d %H:%M")
    print 'Last Run timestamp: %s' % (curTimestamp)
    
    url = 'http://www.pesobility.com/stock'
    
    #trick the server of pesobility to think that you are accessing through
    #   the use of a web browser
    req = urllib2.Request(url, headers={'User-Agent' : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30"}) 
    con = urllib2.urlopen(req)
    
    #copy the html text downloaded from the server
    html_text = con.read()
    
    #parse the html using beautiful soup library
    soup = BeautifulSoup(html_text, 'html.parser')
    
    #Get the update text to know what time is the data from
    updateText = soup.find(id='TOP_WRAPPER').div.div.div
    textStart = string.find(updateText.span.text, ' ') + 1
    
    #Check the text for "today" before proceeding with the extraction 
    textToday = (updateText.span.text)[:textStart-1]
    if textToday != "Today":
        print "Last update of data source was %s." % (textToday)
        print "Old data... No current price data for today yet..."
        return
    
    timeStringRaw = (updateText.span.text)[textStart:]
    timeStringRaw = timeStringRaw.replace(".", "")
    timeMilitary = datetime.datetime.strptime(timeStringRaw, "%I:%M %p").strftime("%H:%M")
    timeMilitary = time.strftime("%Y-%m-%d") + " " + timeMilitary
    
    print "Timestamp for values: %s" % (timeMilitary)
    
    #Get most recent timestamp
    latestTS = qs.GetLatestTimestamp("current_prices")
    
    try:
        latestTS = latestTS.strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        pass

    #Proceed only if the current timestamp is greater than the latest
    #   timestamp in the database
    if timeMilitary > latestTS:
        print "Proceed with inserting current prices"
    else:
        print "Current prices are still up-to-date!"
        return
    
    #Get the list of companies
    companyList = soup.find_all('tr')
    
    #Get most recent entryid
    latestid = qs.GetLatestEntryId("current_prices")    
    if latestid == None:
        latestid = 0  
    
    #Create a dataframe
    df = pd.DataFrame()    
    
    #Process all companies
    for link in companyList:
        company = link.td.a.text
        
        price = link.contents[5]
        priceTextEnd = string.find(price.text, ' ')
        priceText = (price.text)[:priceTextEnd]
        #print "%s Price: %s" % (company, priceText)
        
        latestid = latestid + 1
        data = {'entryid': latestid, 'current': priceText, 'timestamp': timeMilitary, 'company': company}
        df = df.append(data, ignore_index=True)
    
    #set the index to entryid
    df = df.set_index(['entryid'])
    df.index.names = ["entryid"]
    
    qs.PushDBDataFrame(df, "current_prices")   
    print "Finished inserting new data!"
    
    
#Download current prices data from codesword
def downloadCurrentPricesDataCodesword():
    curTimestamp = time.strftime("%Y-%m-%d %H:%M")
    print 'Last Run timestamp: %s' % (curTimestamp)
    
    #Get most recent timestamp
    latestTS = qs.GetLatestTimestamp("current_prices")
    
    try:
        latestTS = latestTS.strftime("%Y-%m-%d+%H:%M:%S")
    except AttributeError:
        print "downloadCurrentPricesDataCodesword(): AttributeError"

    #Download all current price data with timestamp greater than latestTS
    #   from codesword.com
    url = "http://www.codesword.com/getData.php?allcur&lastupdate=%s" % (latestTS)
    r = requests.get(url)

    try:
        df = pd.DataFrame(r.json())
    except TypeError:
        print "    No data..."
        return
    except:
        print "    Database is still up to date"
        return
    
    #Get most recent entryid
    latestid = qs.GetLatestEntryId("current_prices")    
    if latestid == None:
        latestid = 0  
    
    #Update the indeces using the latestid
    df.index = df.index + latestid + 1    
    
    #set the index name to entryid
    df.index.names = ["entryid"]
    
    #insert new information on the "current_prices" table
    qs.PushDBDataFrame(df, "current_prices")   
    print "Finished inserting new data!\n"

    #calculate new ohlcurrent and insert to "current_ohlc" table    
    calcOHLCurrentAll()
    
#Calculate the current OHLC for a company
def calcOHLCurrent(company = None):
    if (company == None) or (company == ""):
        print "No company selected"
        return
    else:
        #Add steps calculate the current OHLC for the selected company
        data = qs.calculateOHLCurrent(company)
        #print ohlCurrent
        ohlCur = data[0]
        
        #Insert the values to the database
        qs.insertOHLCurrent(company,ohlCur[1],ohlCur[2],ohlCur[3],ohlCur[4],ohlCur[5])
        

#Calculate all current OHLC of companies
def calcOHLCurrentAll():
    companies = qs.GetQuoteNamesToUpdate()
    print "Generating OHLCurrent of stocks... "    
    
    for data in companies:
        strlength = len(data[0])
        company = data[0][0:strlength-1]  
        
        #print company
        print company + ", ",
        calcOHLCurrent(company)
        
    print "finished generation of OHLCurrent"


def createCurrentPricesTable():
    #Create the current_prices table if it doesn't exist yet
    doesTableExist = qs.checkTableExistence("current_prices")       

    if doesTableExist == 0:
        #create table before adding
        print "creating table current_prices!"
        qs.createCurrentPricesTable()
        
def createCurrentOHLCTable():
    #Create the current_ohlc table if it doesn't exist yet
    doesTableExist = qs.checkTableExistence("current_ohlc")         

    if doesTableExist == 0:
        #create table before adding
        print "creating table current_ohlc!"
        qs.createOHLCurrentTable()


#createCurrentPricesTable()
#downloadCurrentPricesData()
#calcOHLCurrent("tel")
#calcOHLCurrentAll()