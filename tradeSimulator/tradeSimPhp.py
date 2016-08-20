# -*- coding: utf-8 -*-
"""
Created on Sat Aug 20 10:26:01 2016

@author: CogProm
"""
import os
import sys
import pandas as pd
import numpy as np
import time
import json
import pandas as pd
import urllib2
import sys

#include the path of "Data Analysis" folder for the python scripts searching
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1,path)
del path    

import queryStockDb as qs

#Initialize the data frames for all buy and sell signals of all stocks
allBuys = pd.DataFrame()
allSells = pd.DataFrame()

def getTradeSignals(company):
    global allBuys
    global allSells    
    
    try:
        url = 'http://localhost/stana/getData.php?company=%s&chart=smaentryatrstop&period=20&timerange=1y&enprofit=false' % company
        response = urllib2.urlopen(url).read()
    
        trimmedJson = response.strip()
        
        # All Signals
        securitySignalsAll = json.loads(trimmedJson)
        securityBuy = securitySignalsAll['buy']
        securitySell = securitySignalsAll['sell']
        
        # Store the Buy and Sell signals to the dataframe variables
        allBuys = allBuys.append(pd.DataFrame(securityBuy), ignore_index=True)
        allSells = allSells.append(pd.DataFrame(securitySell), ignore_index=True)
        
#        print trimmedJson
    except:
        print "Error: No Data for %s" % company 

#Run the trade simulator
def runTradeSimulator():
    securities = qs.GetQuoteNamesToUpdate()
    #print securities

    for companyInfo in securities:
        security = companyInfo[0].replace("_","")
        print security
        
        getTradeSignals(security)
    
    
runTradeSimulator()




















