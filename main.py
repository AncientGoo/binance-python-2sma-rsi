from apikey import Keys
from functions.main_functions import *

Symbols = {'BNBBUSD': [0.02, 2],
           #'SOLBUSD': [1, 2],
           'ADABUSD': [7, 4],
           'XRPBUSD': [8, 4],
           'DOGEBUSD': [38, 5],
           'ETHBUSD': [0.002, 2],
           'FTTBUSD': [0.2, 3],
           }


Interval = '6h'
Limit = 500
leverage = 1 

def ping_binance(api):
    ping = None
    while ping != {}:
        try:
            ping = api.client.ping()
        except:
            time.sleep(30)
            pass
        
        
if __name__ == "__main__":

    api = connect_to_api(Keys.public, Keys.private, Symbols, leverage)

    
    Crypto_Currencies = get_CCs_historical(api, Symbols, Interval, Limit)

    while True:
        for crypto_currency in Crypto_Currencies:
            # print('Switch to ', crypto_currency.symbol)
            try:
                trade(crypto_currency, api)
            except Exception as ex:
                print(ex)
                ping_binance(api)
                pass

                  




