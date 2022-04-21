from apikey import Keys
from functions.main_functions import *

Symbols = {'BNBBUSD': 0.02,
           'SOLBUSD': 1,
           'ADABUSD': 6,
           'XRPBUSD': 7,
           'DOGEBUSD': 36}


Interval = '6h'
Limit = 500
leverage = 1 



if __name__ == "__main__":

    api = connect_to_api(Keys.public, Keys.private, Symbols, leverage)

    
    Crypto_Currencies = get_CCs_historical(api, Symbols, Interval, Limit)

    while True:
        for crypto_currency in Crypto_Currencies:
            # print('Switch to ', crypto_currency.symbol)
            trade(crypto_currency, api)

                  




