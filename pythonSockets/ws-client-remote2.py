# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:59:18 2016

@author: PradoArturo
"""

from datetime import datetime
import dewsSocketLeanLib as dsll

#msg = "~`!@#$%^&*()_-+=qwertyuiop[]asdfghjkl;"
#msg = "Are we back in business?"
msg = "codesword recommendations"
curTS = datetime.now()
#dsll.sendReceivedGSMtoDEWS(curTS, "09167777777", msg)
#dsll.sendReceivedGSMtoDEWS(curTS, "09168888888", msg)
dsll.sendToWSSToGSM(curTS, "09980619501", msg)