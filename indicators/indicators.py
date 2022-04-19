import pandas as pd
import ta
import numpy as np
from talipp.indicators import TSI, MACD

class Indicators:
    @staticmethod
    def RSI(crypto_currency):
        close_array = np.asarray(crypto_currency.close_values)
        close_finished = close_array #[1:] #.squeeze(1)
        rsi = ta.momentum.rsi(pd.DataFrame(close_finished)[0])
        return rsi

    @staticmethod
    def AVG_Volume(crypto_currency, w=3):
        volume_array = np.asarray(crypto_currency.volume)
        avg_volume = volume_array[-w:].mean()
        return avg_volume

    @staticmethod
    def ROC(crypto_currency, w=90):
        close_finished = np.asarray(crypto_currency.close_values) # [-w-1:]

        roc = ta.momentum.roc(pd.DataFrame(close_finished)[0], window=w).values
        return roc

    @staticmethod
    def SMA(crypto_currency, w=180):
        close_finished = np.asarray(crypto_currency.close_values)[-w-1:]
        sma = ta.trend.sma_indicator(pd.DataFrame(close_finished)[0], window=w)
        return sma

    @staticmethod
    def DPO(crypto_currency, w=14):
        close_finished = np.asarray(crypto_currency.close_values)[-50:]
        dpo = ta.trend.dpo(pd.DataFrame(close_finished)[0], window=w).values
        #dpo = DPO(period=21, input_values=close_finished)
        return dpo

    @staticmethod
    def MACD(crypto_currency, wf=6, ws=21):
        close_finished = np.asarray(crypto_currency.close_values)[-43:]
        #macd = ta.trend.macd(pd.DataFrame(close_finished)[0], window_fast=wf, window_slow=ws).values
        macd = MACD(fast_period=wf, slow_period=ws, signal_period=wf, input_values=close_finished)
        return macd.to_lists()["histogram"]