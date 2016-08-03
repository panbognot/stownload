# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:59:18 2016

@author: PradoArturo
"""

from datetime import datetime
import os, sys
import currentPricesLib as cpl
import queryStockDb as qs

#include the path of "Data Analysis" folder for the python scripts searching
path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pythonSockets'))
if not path in sys.path:
    sys.path.insert(1,path)
del path    

import dewsSocketLeanLib as dsll

topGainers = qs.getTopGainers(15);
lastTS = topGainers[0][0]
msg = "codesword recommendations (%s):\n" % (lastTS)
for gainer in topGainers:
    msg = msg + "%s %s%%\n" % (gainer[1], gainer[2])

curTS = datetime.now()
dsll.sendToWSSToGSM(curTS, "09980619501", msg)
dsll.sendToWSSToGSM(curTS, "09988987161", msg)