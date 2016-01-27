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

def readDropboxStockQuotes (myFile):
    with open(myFile,'rb') as f:
        reader = csv.reader(f)
        
        header = ['Quote','Date','Open','High','Low','Close','Volume','Unknown']    
        jsonData = []
        
        rownum = 0
        for row in reader:
            #print row
            temp = []
            colnum = 0
            for col in row:
                #jsonCol = header[colnum]
                #print '%s: %s' % (jsonCol, col)
                temp.append(col)
                colnum += 1
                
            try:
                temp[1] = datetime.datetime.strptime(temp[1], "%m/%d/%Y").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                temp[1] = datetime.datetime.strptime(temp[1], "%m-%d-%Y").strftime("%Y-%m-%d %H:%M:%S")
            
            '''        
            jsonData.append({header[0]: temp[0], header[1]: temp[1], \
                            header[2]: temp[2], header[3]: temp[3], \
                            header[4]: temp[4], header[5]: temp[5], \
                            header[6]: temp[6], header[7]: temp[7]})
            '''
            tempQuote = temp[0]
            tempQuote = tempQuote.replace("^", "_")
            tempQuote = tempQuote.replace("-", "_")
            tempQuote += "_"
            doesTableExist = qs.checkTableExistence(tempQuote)       
            #print "does quote: %s have a table? %s" % (tempQuote, doesTableExist) 
            
            if doesTableExist:
                #insert data to database
                print "%s table exists... writing data..." % tempQuote
                qs.writeQuoteDataToDB(tempQuote,temp,"dropbox")
            else:
                #create table before adding
                print "creating table %s!" % tempQuote
                qs.createTable(tempQuote)
                print "    writing data to %s" % tempQuote            
                qs.writeQuoteDataToDB(tempQuote,temp,"dropbox")
                
            rownum += 1

#Go through all the csv file and import them to the database
for root, dirs, files in os.walk("StockQuotes"):
    for file in files:
        if file.endswith(".csv"):
            fullPath = os.path.join(root, file)
            #print(fullPath)
            
            readDropboxStockQuotes(fullPath)
            
            
            
            
            
            