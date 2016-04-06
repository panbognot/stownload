# -*- coding: utf-8 -*-
"""
Created on Sat Dec 05 02:30:38 2015

@author: PradoArturo
"""

import csv
import sys
import json
import re
import queryStockDb as qs
import datetime
import glob, os
import urllib2
import time
from datetime import timedelta as td
import pandas as pd

def downloadPseCSVdata(quoteData):
    #file to be written to
    tempFile = "stockquote.csv"

    #segregate the data
    company = quoteData[0]    
    id = quoteData[1]
    security = quoteData[2]
    
    doesTableExist = qs.checkTableExistence(company)       
    #print "does quote: %s have a table? %s" % (company, doesTableExist)    

    if doesTableExist == 0:
        #create table before adding
        print "creating table %s!" % company
        qs.createTable(company)
        
    latestTS = qs.GetLatestTimestamp(company)
        
    if latestTS == None:
        latestTS = "1900-01-01 00:00:00"
    
    try:
        latestTS = latestTS.strftime("%Y-%m-%d %H:%M:%S.0")
    except AttributeError:
        latestTS = datetime.datetime.strptime(latestTS, "%Y-%m-%d %H:%M:%S")
        
    #Quick Check if stocks data has been updated for today
    curTS = time.strftime("%Y-%m-%d 00:00:00.0")
    #print "timestamp today: %s" % (curTS)
    if curTS == latestTS:
        print "company: %s, id: %s, security: %s, stock is UP TO DATE!!!" % (company, id, security)
        return
    else:
        #Current timestamp
        curTS = time.strftime("%Y-%m-%d %H:%M:%S.0")
        #Philippine Market Close Time
        targetTS = time.strftime("%Y-%m-%d 15:35:00.0")
        prevTS = (pd.to_datetime("2016-03-11") - td(1)).strftime("%Y-%m-%d 00:00:00.0")
        if (latestTS == prevTS) and (curTS < targetTS):
            print "company: %s, id: %s, security: %s, stock is UP TO DATE!!!" % (company, id, security)
            return
            #pass
        
        print "company: %s, id: %s, security: %s, latest timestamp: %s" % (company, id, security, latestTS)
    
    url = 'http://pse.ph/stockMarket/companyInfoHistoricalData.html?method=downloadHistoricData&ajax=true&security=%s' % (security)
    response = urllib2.urlopen(url)
    
    print "The Headers are: ", response.info()['content-disposition']  
    
    try:
        # Get all data
        html = response.read()
        time.sleep(1)
        #print "Get all date:", html
        
        #open the file for writing
        fh = open(tempFile,"w")
        fh.write(html)
        fh.close()
        
        with open(tempFile,'rb') as f:
            reader = csv.reader(f)
            header = []    
            
            rownum = 0
            for row in reader:
                if rownum == 0:
                    header = row
                    rownum += 1
                    #print header
                    continue
                
                #print row
                temp = []
                colnum = 0
                for col in row:
                    temp.append(col)
                    colnum += 1
                    
                if temp[0] > latestTS:
                    # write to database only if the timestamp is greater than
                    # the latest timestamp
                    print "Writing row with timestamp: %s" % (temp[0])
                    qs.writeQuoteDataToDB(company,temp,"pse")
                
                rownum += 1
    except:
        print "\nERROR: Info might be wrong for company: %s, id: %s, security: %s\n" % (company, id, security) 

stocks_list = qs.GetQuoteNamesToUpdate()

entryid = 1
startid = 0
for stock in stocks_list:
    if entryid > startid:
        downloadPseCSVdata(stock)
        
    entryid += 1

#downloadPseCSVdata(["apx_",178,318])











            
            
            
            
            
            