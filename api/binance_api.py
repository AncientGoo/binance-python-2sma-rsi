from binance.client import Client
from binance.futures import Futures
from models.crypto_currency import CryptoCurrency
import numpy as np

class Binance:
    client = ""
    def __init__(self, api_key="Key", api_secret="Secret"):
        if api_key != "Key" and api_secret != "Secret":
            Binance().connect_to_api(api_key, api_secret)
        else:
            self.api_key = api_key
            self.api_secret = api_secret

    def connect_to_api(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(self.api_key, api_secret)
        self.Futures_client = Futures(self.api_key, api_secret)

    def get_api_key(self):
        print("Your Api Key: {}".format(self.api_key))

    def get_api_secret(self):
        print("Your Api Secret: {}".format(self.api_secret))

    def get_historical_data(self, crypto_currency):
        klines = self.client.futures_klines(symbol=crypto_currency.symbol, interval=crypto_currency.interval, limit=crypto_currency.limit) # Get futures klines
        #crypto_currency = CryptoCurrency(symbol, interval, limit, order_qty)

        for i in range(crypto_currency.limit):

            crypto_currency.open_time[i] = int(klines[i][0])
            crypto_currency.open_values[i] = float(klines[i][1])
            crypto_currency.high_values[i] = float(klines[i][2])
            crypto_currency.low_values[i] = float(klines[i][3])
            crypto_currency.close_values[i] = float(klines[i][4])
            crypto_currency.volume[i] = float(klines[i][5])
        
        return crypto_currency


    def get_crypto_currency_update(self, crypto_currency):
        klines = self.client.futures_klines(symbol=crypto_currency.symbol, interval=crypto_currency.interval, limit=2) # Get futures klines

        if (int(klines[1][0]) - crypto_currency.open_time[-1]) == 0:
            crypto_currency.open_time[-1] = int(klines[1][0])
            crypto_currency.open_values[-1] = float(klines[1][1])
            crypto_currency.high_values[-1] = float(klines[1][2])
            crypto_currency.low_values[-1] = float(klines[1][3])
            crypto_currency.close_values[-1] = float(klines[1][4])
            crypto_currency.volume[-1] = float(klines[1][5])


        else:
            crypto_currency.open_time[-1] = int(klines[0][0])
            crypto_currency.open_values[-1] = float(klines[0][1])
            crypto_currency.high_values[-1] = float(klines[0][2])
            crypto_currency.low_values[-1] = float(klines[0][3])
            crypto_currency.close_values[-1] = float(klines[0][4])
            crypto_currency.volume[-1] = float(klines[0][5])

            crypto_currency.open_time.pop(0)
            crypto_currency.open_values.pop(0)
            crypto_currency.high_values.pop(0)
            crypto_currency.low_values.pop(0)
            crypto_currency.close_values.pop(0)
            crypto_currency.volume.pop(0)
        
            crypto_currency.open_time.append(int(klines[0][0]))
            crypto_currency.open_values.append(float(klines[0][1]))
            crypto_currency.high_values.append(float(klines[0][2]))
            crypto_currency.low_values.append(float(klines[0][3]))
            crypto_currency.close_values.append(float(klines[0][4]))
            crypto_currency.volume.append(float(klines[0][5]))



        crypto_currency.current_kline_time = int(klines[0][0])



