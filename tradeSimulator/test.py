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
        
df = getSOHLCAVV('smc', '2016-03-16')

if df.empty:
    print "empty dataframe"
else:
    print df
    
if (float)(df.iloc[0]['value']) < 1000000:
    print "stock is filtered out"
else:
    print "stock passes filter"
    valueLimit = 50000
    buyPrice = (float)(df.iloc[0]['close'])
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
    
    priceBuyLot = lotSize * buyPrice
    valueBought = valueLimit - (valueLimit % priceBuyLot)
    volumeBought = valueBought * lotSize / priceBuyLot
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    