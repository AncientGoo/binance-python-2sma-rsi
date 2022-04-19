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

    def get_historical_data(self, symbol, interval, limit):
        klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit) # Get futures klines
        self.crypto_currency = CryptoCurrency(symbol, interval, limit)

        for i in range(limit):
            self.crypto_currency.open_time[i] = int(klines[i][0])
            self.crypto_currency.open_values[i] = float(klines[i][1])
            self.crypto_currency.high_values[i] = float(klines[i][2])
            self.crypto_currency.low_values[i] = float(klines[i][3])
            self.crypto_currency.close_values[i] = float(klines[i][4])
            self.crypto_currency.volume[i] = float(klines[i][5])
        
        return self.crypto_currency


    def get_crypto_currency_update(self, kline):
        klines = kline  # self.client.futures_klines(symbol=symbol, interval=interval, limit=1) # Get futures klines

        if (int(klines[0][0]) - self.crypto_currency.open_time[-1]) < 60000:
            self.crypto_currency.open_time[-1] = int(klines[0][0])
            self.crypto_currency.open_values[-1] = float(klines[0][1])
            self.crypto_currency.high_values[-1] = float(klines[0][2])
            self.crypto_currency.low_values[-1] = float(klines[0][3])
            self.crypto_currency.close_values[-1] = float(klines[0][4])
            self.crypto_currency.volume[-1] = float(klines[0][5])


        else:
            self.crypto_currency.open_time.pop(0)
            self.crypto_currency.open_values.pop(0)
            self.crypto_currency.high_values.pop(0)
            self.crypto_currency.low_values.pop(0)
            self.crypto_currency.close_values.pop(0)
            self.crypto_currency.volume.pop(0)
        
            self.crypto_currency.open_time.append(int(klines[0][0]))
            self.crypto_currency.open_values.append(float(klines[0][1]))
            self.crypto_currency.high_values.append(float(klines[0][2]))
            self.crypto_currency.low_values.append(float(klines[0][3]))
            self.crypto_currency.close_values.append(float(klines[0][4]))
            self.crypto_currency.volume.append(float(klines[0][5]))



        current_kline_time = int(klines[0][0])

        return current_kline_time


