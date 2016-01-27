import pymysql
import ConfigParser
from datetime import datetime as dtm
from datetime import timedelta as tda
import re
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import StringIO
import time

# Scripts for connecting to local database
def StockDBConnect(nameDB):
    while True:
        try:
            db = pymysql.connect(host = Hostdb, user = Userdb, passwd = Passdb, db=nameDB)
            cur = db.cursor()
            return db, cur
        except pymysql.OperationalError:
            print '.',

def PrintOut(line):
    if printtostdout:
        print line

def createTable(table_name):
    db, cur = StockDBConnect(Namedb)
    cur.execute("CREATE DATABASE IF NOT EXISTS %s" %Namedb)
    cur.execute("USE %s"%Namedb)
    
    cur.execute("CREATE TABLE IF NOT EXISTS %s(timestamp datetime, \
                open float, high float, low float, close float, \
                average float, volume int, value float, unknown float, \
                PRIMARY KEY (timestamp))" %table_name)
        
    db.close()
    
def checkTableExistence(table):
    db, cur = StockDBConnect(Namedb)
    query = "SHOW TABLES LIKE '%s'" % table
    #print query
    ret = 0
    try:
        a = cur.execute(query)
        ret = cur.fetchall()[0][0]
    except TypeError:
        print "Error"
        ret = 0
    finally:
        db.close()
        return ret

def GetQuoteNamesToUpdate():
    db, cur = StockDBConnect(Namedb)
    #cur.execute("CREATE DATABASE IF NOT EXISTS %s" %nameDB)
    try:
        query = "SELECT lower(stock_quotes.quote) AS quote, id, security FROM stock_quotes"
        cur.execute(query)
    except:
        print "Error in getting stock quotes list"

    ret = cur.fetchall()
    db.close()    
    if ret:
        return ret
    else: 
        return ''

def GetLatestTimestamp(quote):
    db, cur = StockDBConnect(Namedb)
    #cur.execute("CREATE DATABASE IF NOT EXISTS %s" %nameDB)
    try:
        cur.execute("select max(timestamp) from %s.%s" %(Namedb,quote))
    except:
        print "Error in getting maximum timestamp"

    a = cur.fetchall()
    if a:
        return a[0][0]
    else: 
        return '0000-00-00 00:00:00'

def writeQuoteDataToDB(quote,curData,source):
    query = """INSERT IGNORE INTO %s (timestamp,open,high,low,close,average,volume,value,unknown) VALUES """ % quote.lower()

    db, cur = StockDBConnect(Namedb)

    if source == "dropbox":
        query = query + """('%s',%s,%s,%s,%s,null,%s,null,%s)""" % \
                (str(curData[1]),str(curData[2]),str(curData[3]), \
                str(curData[4]),str(curData[5]),str(curData[6]), \
                str(curData[7]))
    elif source == "pse":
        query = query + """('%s',%s,%s,%s,%s,%s,%s,%s,null)""" % \
                (str(curData[0]),str(curData[1]),str(curData[2]), \
                str(curData[3]),str(curData[4]),str(curData[5]), \
                str(curData[6]),str(curData[7]))

    #print query

    try:
        retry = 0
        while True:
            try:
                a = cur.execute(query)
                if a:
                    db.commit()
                    break
                else:
                    print '>> Warning: Query has no result set (writeQuoteDataToDB)'
                    break
            except pymysql.OperationalError:
                print '5.',
                if retry > 10:
                    return
                else:
                    retry += 1
            except pymysql.ProgrammingError:
                print ">> Unable to write to table '" + quote + "'"
                return
                    
            
    except KeyError:
        print '>> Error: Writing to database'
    except pymysql.IntegrityError:
        print '>> Warning: Duplicate entry detected'
        
            
    db.close()

#GetSensorList():
#    returns a list of columnArray objects from the database tables
#    
#    Returns:
#        sensorlist: list
#            list of columnArray (see class definition above)

#def GetSensorList():
#    try:
#        db, cur = StockDBConnect(Namedb)
#        cur.execute("use "+ Namedb)
#        
#        query = 'SELECT name, num_nodes, seg_length, col_length FROM site_column_props'
#        
#        df = psql.read_sql(query, db)
#        df.to_csv("column_properties.csv",index=False,header=False);
#        
#        # make a sensor list of columnArray class functions
#        sensors = []
#        for s in range(len(df)):
#            s = columnArray(df.name[s],df.num_nodes[s],df.seg_length[s],df.col_length[s])
#            sensors.append(s)
#        return sensors
#    except:
#        raise ValueError('Could not get sensor list from database')
#
#def GetSensorDF():
#    try:
#        #db, cur = StockDBConnect(Namedb)
#        #cur.execute("use "+ Namedb)
#        
#        query = 'SELECT name, num_nodes, seg_length, col_length FROM site_column_props'
#        
#        #df = psql.read_sql(query, db)
#        
#        df = GetDBDataFrame(query)
#        return df
#    except:
#        raise ValueError('Could not get sensor list from database')
            
# import values from config file
configFile = "server-config.txt"
cfg = ConfigParser.ConfigParser()

try:
    cfg.read(configFile)
    
    DBIOSect = "DB I/O"
    Hostdb = cfg.get(DBIOSect,'Hostdb')
    Userdb = cfg.get(DBIOSect,'Userdb')
    Passdb = cfg.get(DBIOSect,'Passdb')
    Namedb = cfg.get(DBIOSect,'Namedb')
    printtostdout = cfg.getboolean(DBIOSect,'Printtostdout')
    
    valueSect = 'Value Limits'
    xlim = cfg.get(valueSect,'xlim')
    ylim = cfg.get(valueSect,'ylim')
    zlim = cfg.get(valueSect,'zlim')
    xmax = cfg.get(valueSect,'xmax')
    mlowlim = cfg.get(valueSect,'mlowlim')
    muplim = cfg.get(valueSect,'muplim')
    islimval = cfg.getboolean(valueSect,'LimitValues')
except:
    #default values are used for missing configuration files or for cases when
    #sensitive info like db access credentials must not be viewed using a browser
    print "No file named: %s. Trying Default Configuration" % (configFile)
    Hostdb = "127.0.0.1"
    Userdb = "root"
    Passdb = "senslope"
    Namedb = "pse_data"
    printtostdout = False
    
    xlim = 100
    ylim = 1126
    zlim = 1126
    xmax = 1200
    mlowlim = 2000
    muplim = 4000
    islimval = True   






