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
from datetime import datetime, timedelta
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
#TODO: company,shares,buyprice,sellprice,datebought,datesold,profit
stocksHeld = pd.DataFrame()

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

def getSOHLCAVV(company, targetdate):
    try:
        url = 'http://localhost/stana/getData.php?company=%s&chart=sohlcavv&targetdate=%s' % (company, targetdate)
        response = urllib2.urlopen(url).read()
    
        trimmedJson = response.strip()
        
        # ohlcavv
        sohlcavv = json.loads(trimmedJson)
        sohlcavv[0]['company'] = company
        
#        return sohlcavv
        return pd.DataFrame(sohlcavv)
    except:
        print "Error: No Data for %s" % company 
        return pd.DataFrame()    

#Run the trade simulator
def runTradeSimulator():
    securities = qs.GetQuoteNamesToUpdate("a")
    #print securities

    #Get the trade signals for all stocks
    for companyInfo in securities:
        security = companyInfo[0].replace("_","")
        print security
        
        getTradeSignals(security)
        
    #TODO: Select starting date (for now: 6 month trading period)
    tradingPeriodMonths = 3
    timeDelta = tradingPeriodMonths * 30
    dFormat = "%Y-%m-%d"
    
    tradingEndDate = datetime.now()
    tradingStartDate = tradingEndDate - timedelta(days=timeDelta)
    dCtr = 0    
    
    #TODO: Initial capital (for now: unlimited funds)
    capital = 500000
    valueLimit = 50000
    holdLimit = 10

    global stocksHeld
    
    while dCtr <= timeDelta:
        tradingCurDate = tradingStartDate + timedelta(days=dCtr)
        curDate = tradingCurDate.strftime(dFormat)
        print curDate

        #Get the buy options list
        buyOptions = allBuys[allBuys['date']==curDate]

        for index, row in buyOptions.iterrows():
            #Get the OHLCAVV of each buy option            
            tempCompany = row['company']
            ohlcavv = getSOHLCAVV(tempCompany, curDate)
            
            try:
                #filter out stocks with low activity (low value) 
                if (float)(ohlcavv.iloc[0]['value']) < 500000:
                    #filter out stocks with trade value less than 1 Million (arbitrary value)
                    buyOptions = buyOptions[buyOptions.company != tempCompany]
                    continue
                
                #TODO: filter out stocks that are on a down trend
                
                #Buy the stock if it passes the filters
                buyPrice = (float)(ohlcavv.iloc[0]['close'])
                lotSize = 0
    
                if buyPrice < 1:
                    lotSize = 10000    
                elif buyPrice < 10:
                    lotSize = 1000
                elif buyPrice < 100:
                    lotSize = 100
                elif buyPrice < 1000:
                    lotSize = 10
                else:
                    lotSize = 5
                
                try:
                    currentlyOnHold = stocksHeld[stocksHeld.datesold=='tba']
                    holdCount = len(currentlyOnHold.index)
                except:
                    holdCount = 0
                
                if holdCount < holdLimit:            
                    priceBuyLot = lotSize * buyPrice
                    valueBought = valueLimit - (valueLimit % priceBuyLot)
                    volumeBought = valueBought * lotSize / priceBuyLot
        
                    tempJson = [{"company":tempCompany,"shares":volumeBought,"buyprice":buyPrice,"sellprice":"tba","datebought":curDate,"datesold":"tba","profit":0}]
                    stocksHeld = stocksHeld.append(pd.DataFrame(tempJson), ignore_index=True)      
                else:
                    print "Already at maximum hold limit"
            except:
                pass
            
        #Choose from stocks with buy signal
        #TODO: Randomly choose from all the available stocks with buy signal for the day
        if buyOptions.empty:
            print "Nothing to buy for today"
        else:
            print buyOptions
            
        #TODO: Sell when there is a "sell: cut losses"
        #from the list of stocks you are holding
        sellOptions = allSells[(allSells['date']==curDate) & (allSells['signal']=='sell: cut losses')]
            
        if sellOptions.empty:
            print "Nothing to sell for today"
        else:
#            print sellOptions
            
            if not stocksHeld.empty: 
                for index, row in sellOptions.iterrows():
                    tempCompany = row['company']        
                    tempHeldData = stocksHeld[(stocksHeld['company']==tempCompany) & (stocksHeld['datesold']=="tba")]
                    
                    if not tempHeldData.empty:
                        ohlcavv = getSOHLCAVV(tempCompany, curDate)
                        
                        buyPrice = (float)(tempHeldData.iloc[0]['buyprice'])
                        shares = (float)(tempHeldData.iloc[0]['shares'])
                        sellPrice = (float)(ohlcavv.iloc[0]['close'])
                        
                        profit = (sellPrice - buyPrice) * shares                        
                        
                        stocksHeld.datesold[(stocksHeld.datesold=='tba') & (stocksHeld.company==tempCompany)] = curDate
                        stocksHeld.sellprice[(stocksHeld.datesold==curDate) & (stocksHeld.company==tempCompany)] = sellPrice
                        stocksHeld.profit[(stocksHeld.datesold==curDate) & (stocksHeld.company==tempCompany)] = profit
                        pass
            
        #TODO: Record the profit level per day
            
        #Increment the day counter
        dCtr = dCtr + 1
    
runTradeSimulator()

#TODO: Sell the stocks being held

print "Total Profit: %s" % (stocksHeld['profit'].sum())





































































