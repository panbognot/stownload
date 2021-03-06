#import MySQLdb
import ConfigParser
from datetime import datetime as dtm
from datetime import timedelta as tda
import re
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import StringIO
import time
import platform

curOS = platform.system()

if curOS == "Windows":
    if platform.machine().endswith('86'):
        import pymysql as mysqlDriver
    else:
        import MySQLdb as mysqlDriver
elif curOS == "Linux":
    import pymysql as mysqlDriver

# Scripts for connecting to local database
def StockDBConnect(nameDB):
    while True:
        try:
            db = mysqlDriver.connect(host = Hostdb, user = Userdb, passwd = Passdb, db=nameDB)
            cur = db.cursor()
            return db, cur
        except mysqlDriver.OperationalError:
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
    
def createCurrentPricesTable():
    db, cur = StockDBConnect(Namedb)
    
    cur.execute("CREATE TABLE IF NOT EXISTS current_prices( \
                `entryid` INT NOT NULL AUTO_INCREMENT, \
                `timestamp` DATETIME NULL, \
                `company` VARCHAR(16) NULL, \
                `current` FLOAT NULL, \
                PRIMARY KEY (`entryid`)) \
                ENGINE = InnoDB \
                DEFAULT CHARACTER SET = utf8 \
                COMMENT = 'table for storing the current prices of the downloaded stock data';")
    db.close()    
    
def createOHLCurrentTable():
    db, cur = StockDBConnect(Namedb)
    
    cur.execute("CREATE TABLE IF NOT EXISTS current_ohlc( \
                `company` VARCHAR(16) NULL, \
                `timestamp` DATETIME NULL, \
                `open` FLOAT NULL, \
                `high` FLOAT NULL, \
                `low` FLOAT NULL, \
                `close` FLOAT NULL, \
                PRIMARY KEY (`company`)) \
                ENGINE = InnoDB \
                DEFAULT CHARACTER SET = utf8 \
                COMMENT = 'table for storing the current prices of the downloaded stock data';")
    db.close()
    
def createCurrentTopGainersTable():
    db, cur = StockDBConnect(Namedb)
    
    cur.execute("CREATE TABLE IF NOT EXISTS current_gainers( \
                `entryid` INT NOT NULL AUTO_INCREMENT, \
                `company` VARCHAR(16) NOT NULL, \
                `timestamp` DATETIME NOT NULL, \
                `percentage` FLOAT NOT NULL, \
                PRIMARY KEY (`entryid`)) \
                ENGINE = InnoDB \
                DEFAULT CHARACTER SET = utf8 \
                COMMENT = 'table for storing the current prices of the downloaded stock data';")
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

def ExecuteQuery(query, db = None, cur = None):
    useNewConn = True    
    
    if (db != None) and (cur != None):
        useNewConn = False
    
    if useNewConn:
        db, cur = StockDBConnect(Namedb)
    #print query
    ret = 0
    try:
        a = cur.execute(query)
        if a:
            db.commit()
        else:
            PrintOut('>> Warning: Query has no result set (ExecuteQuery)')
        
        ret = cur.fetchall()
    except TypeError:
        print "ExecuteQuery: Error"
        ret = 0
    finally:
        if useNewConn:
            db.close()
        
        return ret
        
def getDayPrices(company=None, db=None, cur=None):
    if company == None:
        print "No company selected"
        return
    
    query = "SELECT * FROM current_prices WHERE company = '%s' " % (company)
    query += "AND timestamp > curdate()"
    
    dayPrices = ExecuteQuery(query, db, cur)
    return dayPrices
    
def getOHLCurrent(company=None, db=None, cur=None):
    if company == None:
        print "No company selected"
        return
        
    query = "SELECT * FROM current_ohlc WHERE company = '%s' " % (company)
    
    ohlCurrent = ExecuteQuery(query, db, cur)
    return ohlCurrent
    
def getTopGainers(limit=25, db=None, cur=None):
    query = "SELECT DATE_FORMAT(timestamp,'%b-%d %H:%i') as timestamp, company, percentage FROM current_gainers "
    query += "WHERE timestamp = (SELECT MAX(timestamp) FROM current_gainers) "
    query += "ORDER BY percentage DESC LIMIT %s" % (limit)
    
    topGainers = ExecuteQuery(query, db, cur)
    return topGainers
        
def calculateOHLCurrent(company, db=None, cur=None):
    query = "select "
    query += "'%s' as company, " % (company)
    query += "(select MAX(timestamp) from current_prices where company = '%s') as timestamp," % (company)
    query += "ROUND((select current from current_prices where company = '%s' " % (company)
    query += "AND timestamp > curdate() order by timestamp asc limit 1),4) as open, "
    query += "ROUND(max(current),4) as high," 
    query += "ROUND(min(current),4) as low," 
    query += "ROUND((select current from current_prices where company = '%s'" % (company)
    query += "AND timestamp > curdate() order by timestamp desc limit 1),4) as close "
    query += "from current_prices where company = '%s' AND timestamp > curdate()" % (company)
    
    #print query    
    
    curOHLC = ExecuteQuery(query, db, cur)
    return curOHLC
    
def insertOHLCurrent(company,ts,op,hi,lo,cl,db=None,cur=None):
    query = "INSERT INTO current_ohlc (company, timestamp, open, high, low, close) " 
    query += "VALUES ('%s','%s',%s,%s,%s,%s) " % (company,ts,op,hi,lo,cl)
    query += "ON DUPLICATE KEY UPDATE "
    query += "timestamp='%s',open=%s,high=%s,low=%s,close=%s" % (ts,op,hi,lo,cl)
    
    ExecuteQuery(query, db, cur)  
    pass

def GetQuoteNamesToUpdate(stockClass=None):
    db, cur = StockDBConnect(Namedb)
    #cur.execute("CREATE DATABASE IF NOT EXISTS %s" %nameDB)
    try:
        whereClause = ""        
        
        if stockClass == "bluechip":
            whereClause = "WHERE class like 'Blue Chip' order by quote"
        elif stockClass == "a":
            whereClause = "WHERE class = 'A' or class like 'Blue Chip' order by quote"
            
        query = "SELECT lower(stock_quotes.quote) AS quote, id, security FROM stock_quotes " + whereClause
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
        
def GetLatestEntryId(quote):
    db, cur = StockDBConnect(Namedb)
    #cur.execute("CREATE DATABASE IF NOT EXISTS %s" %nameDB)
    try:
        cur.execute("select max(entryid) from %s.%s" %(Namedb,quote))
    except:
        print "Error in getting maximum entryid"

    a = cur.fetchall()
    if a:
        return a[0][0]
    else: 
        return None

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
            except mysqlDriver.OperationalError:
                print '5.',
                if retry > 10:
                    return
                else:
                    retry += 1
            except mysqlDriver.ProgrammingError:
                print ">> Unable to write to table '" + quote + "'"
                return
                    
            
    except KeyError:
        print '>> Error: Writing to database'
    except mysqlDriver.IntegrityError:
        print '>> Warning: Duplicate entry detected'
        
            
    db.close()

#Push a dataframe object into a table
def PushDBDataFrame(df,table_name):     
    db, cur = StockDBConnect(Namedb)

    df.to_sql(con=db, name=table_name, if_exists='append', flavor='mysql')
    db.commit()
    db.close()
 
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






