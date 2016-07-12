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
import threading
import Queue

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

    #calculate new ohlcurrent and insert to "current_ohlc" table    
    calcOHLCurrentAll(df)    
    
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

#    url = "http://www.codesword.com/getData.php?allcur&lastupdate=%s" % (latestTS)
    url = "http://ec2-54-174-162-14.compute-1.amazonaws.com/codesword.com/html/getData.php?allcur&lastupdate=%s" % (latestTS)    
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
    calcOHLCurrentAll(df)
    
#Calculate the current OHLC for a company
def calcOHLCurrent(company = None, db = None, cur = None, daydata = pd.DataFrame()):
    if (company == None) or (company == ""):
        print "No company selected"
        return
    else:
        curdate = datetime.datetime.now().strftime('%Y-%m-%d') 
        
        try:
            ret = qs.getOHLCurrent(company, db, cur)     
            retTS = (ret[0][1]).strftime('%Y-%m-%d %H:%M:%S')
            retOpen = ret[0][2]
            retHigh = ret[0][3]
            retLow = ret[0][4]
            retCur = ret[0][5]
        except:
            retTS = None             
        
        #Add steps to calculate the current OHLC for the selected company
        if daydata.empty or (retTS == None) or (retTS < curdate): 
            data = qs.getDayPrices(company, db, cur)
            
            try:
                size = len(data)
                prices = []
                
                for elem in data:
                    prices.append(elem[3])
                    
                maxTS = data[size-1][1]
                dOpen = prices[0]
                dHigh = max(prices)
                dLow = min(prices)
                dCur = prices[size-1]
            except:
                print "[No Data for: %s]" % (company)
                return
        else:
            data = daydata[daydata.timestamp > curdate]
            
            size = len(data)
            
            maxTS = data.timestamp.max()
            minTS = data.timestamp.min()
            
            dOpen = data.iloc[0].current
            dHigh = data.current.max()
            dLow = data.current.min()
            dCur = data.iloc[size-1].current
                          
            if retTS > curdate:
                dOpen = retOpen
                
            #Check if maxTS is greater than recorded OHLCurrent timestamp then
            # maintain its value
            if retTS > maxTS:
                maxTS = retTS
                dCur = retCur
            
            #If the recorded OHLCurrent high has a higher high then 
            # maintain its value
            if (retHigh > dHigh) and (retHigh > retOpen) and (retHigh > retCur):
                dHigh = retHigh
                
            #If open price is higher than the current high
            elif (retOpen > dHigh) and (retOpen > retHigh) and (retOpen > retCur):
                dHigh = retOpen
                
            #If returned current price is higher than the current high
            elif (retCur > dHigh) and (retCur > retHigh) and (retCur > retOpen):
                dHigh = retCur
                
            #If the recorded OHLCurrent low has a lower low then
            # maintain its value
            if (retLow < dLow) and (retLow < retOpen) and (retLow < retCur):
                dLow = retLow
                
            #If open price is lower than current low
            elif (retOpen < dLow) and (retOpen < retLow) and (retOpen < retCur):
                dLow = retOpen
                
            #If returned current price is lower than the current low
            elif (retCur < dLow) and (retCur < retLow) and (retCur < retOpen):
                dLow = retCur

        #Insert the values to the database
        qs.insertOHLCurrent(company,maxTS,dOpen,dHigh,dLow,dCur, db, cur)

#Calculate all current OHLC of companies
def calcOHLCurrentAll(df=pd.DataFrame()):
    start = datetime.datetime.now()
    companies = qs.GetQuoteNamesToUpdate()
    print "Generating OHLCurrent of stocks... "   
    
    #Connect to the stocks database
    db, cur = qs.StockDBConnect(qs.Namedb)
    
    for data in companies:
        strlength = len(data[0])
        company = data[0][0:strlength-1]  
        
        #print company
        print company + ", ",
        
        if df.empty:
            calcOHLCurrent(company, db, cur)
        else:
            temp = df[df.company == company.upper()]
            calcOHLCurrent(company, db, cur, temp)
        
    #Close the stocks database connection
    db.close()
        
    print "finished generation of OHLCurrent"
    end = datetime.datetime.now()
    print "processing time: %s" % (end - start)

#download the current prices of stocks
def downloadTopGainersData():
    curTimestamp = time.strftime("%Y-%m-%d %H:%M")
    print 'Last Run timestamp: %s' % (curTimestamp)
    
    url = 'http://www.pesobility.com/reports/top-gainers'
    
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
    latestTS = qs.GetLatestTimestamp("current_gainers")
    
    try:
        latestTS = latestTS.strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        pass

    #Proceed only if the current timestamp is greater than the latest
    #   timestamp in the database
    if timeMilitary > latestTS:
        print "Proceed with inserting Top Gainers"
    else:
        print "Top Gainers are still up-to-date!"
        return

    #Get the table
    companyTableBody = soup.find('tbody')
    
    #Get the list of companies
    #companyList = soup.find_all('tr')
    companyList = companyTableBody.find_all('tr')    
    
    #Get most recent entryid
    latestid = qs.GetLatestEntryId("current_gainers")    
    if latestid == None:
        latestid = 0  
    
    #Create a dataframe
    df = pd.DataFrame()    
    
    #Process all companies
    for link in companyList:
        company = link.contents[3].a.text        
        
        percentage = link.contents[7]
        percTextEnd = string.find(percentage.span.text, '%')
        percText = (percentage.span.text)[:percTextEnd]
        
        latestid = latestid + 1
        data = {'entryid': latestid, 'percentage': percText, 'timestamp': timeMilitary, 'company': company}
        df = df.append(data, ignore_index=True)  
    
    #set the index to entryid
    df = df.set_index(['entryid'])
    df.index.names = ["entryid"]
    
    qs.PushDBDataFrame(df, "current_gainers")   
    print "Finished inserting new data!"

    #calculate new ohlcurrent and insert to "current_ohlc" table    
#    calcOHLCurrentAll(df)   

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

def createCurrentTopGainersTable():
    #Create the current_ohlc table if it doesn't exist yet
    doesTableExist = qs.checkTableExistence("current_gainers")         

    if doesTableExist == 0:
        #create table before adding
        print "creating table current_gainers!"
        qs.createCurrentTopGainersTable()

#createCurrentPricesTable()
#downloadCurrentPricesData()
#calcOHLCurrent("tel")
#calcOHLCurrentAll()


exitFlag = 0
threadList = ["t1","t2","t3","t4","t5","t6","t7","t8"]
queueLock = threading.Lock()
workQueue = 0
threads = []


class myThread (threading.Thread):
    def __init__(self, threadID, name, q, db=None, cur=None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
        self.db = db
        self.cur = cur
    
    def run(self):
        print "Starting " + self.name
        calcOHLCurrentThread(self.name, self.q, self.db, self.cur)
        print "Exiting " + self.name
        

def calcOHLCurrentThread(threadName, q, db=None, cur=None):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            company = q.get()
            calcOHLCurrent(company, db, cur)
            queueLock.release()
            qs.PrintOut("%s processing %s" % (threadName, company))
        else:
            queueLock.release()
        

#Multi Threaded way of calculating OHLCurrent All
def calcOHLCurrentAllMT():
    start = datetime.datetime.now()    
    
    threadID = 1    
    
    companies = qs.GetQuoteNamesToUpdate()
    global workQueue
    workQueue = Queue.Queue(len(companies))
    print "Generating OHLCurrent of stocks... "       
    
    #Connect to the stocks database
    db, cur = qs.StockDBConnect(qs.Namedb)    
    
    #Create new threads
    for tName in threadList:
        thread = myThread(threadID, tName, workQueue, db, cur)
        thread.start()
        threads.append(thread)
        threadID += 1
        
    #Fill the queue
    queueLock.acquire()
    for data in companies:
        strlength = len(data[0])
        company = data[0][0:strlength-1]  
        
        #print company
#        print company + ", ",
#        calcOHLCurrent(company)
        workQueue.put(company)
    queueLock.release()
    
    #Wait for queue to empty
    while not workQueue.empty():
        pass
    
    #Notify threads it's time to exit
    global exitFlag
    exitFlag = 1
    
    #Wait for all threads to complete
    for t in threads:
        t.join()
    
    #Close the stocks database connection
    db.close()    
    
    end = datetime.datetime.now()
    print "processing time: %s" % (end - start)
    
    print "Exiting Main Thread"


#calcOHLCurrentAllMT()
#calcOHLCurrentAll()















