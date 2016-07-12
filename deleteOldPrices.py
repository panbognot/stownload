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

def deleteOldPrices(days = 10):
    #Get current date
    curDate = time.strftime("%Y-%m-%d")
    
    #Get the oldest date that can stay in the "current_prices" table
    oldestDate = (pd.to_datetime(curDate) - td(days)).strftime("%Y-%m-%d")
    
    #compose query for deleting old entries
    query = 'delete from current_prices where timestamp < "%s"' % (oldestDate)  
    query2 = 'delete from current_gainers where timestamp < "%s"' % (oldestDate)
    
    #execute query
    qs.ExecuteQuery(query)
    qs.ExecuteQuery(query2)
    
    pass

deleteOldPrices(1)