import json
import pandas as pd
import subprocess


# if the script don't need output.
#subprocess.call("php C:\\xampp\\htdocs\\stana\\genTradeRecom.php stomacd")

# if you want output
#proc = subprocess.Popen("php C:\\xampp\\htdocs\\stana\\genTradeRecom.php stomacd 60", shell=True, stdout=subprocess.PIPE)
proc = subprocess.Popen("php C:\\xampp\\htdocs\\stana\\getData.php smc", shell=True, stdout=subprocess.PIPE)
response = proc.stdout.read()
trimmedJson = response.strip()

# All Signals
signalsAll = json.loads(trimmedJson)
signalsBuy = signalsAll['buy']
signalsSell = signalsAll['sell']


#print trimmedJson