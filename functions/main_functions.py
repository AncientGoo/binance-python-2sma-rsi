from models.crypto_currency import CryptoCurrency
from indicators.indicators import Indicators
import time
import win32api
import numpy as np
from api.binance_api import Binance


def error_wrapper(func): 
    def wrapper(*args):
        trigger_time = time.time()
        while True:
            try:
                return func(*args)
                break
            except Exception as ex:
                print(ex)
                print('Error in', str(func))
                time.sleep(0.25)
                if time.time()-trigger_time > 30:
                    break
                else:
                    pass

    return wrapper



def get_conditions_to_open_order(crypto_currency):
    sma_slow = Indicators.SMA(crypto_currency, w=200)
    sma_fast = Indicators.SMA(crypto_currency, w=40)

    rsi = Indicators.RSI(crypto_currency)
    # macd = Indicators.MACD(crypto_currency, 40, 200, 20)

    #sma_long_diff = (np.mean(sma_slow[-3:]) / np.mean(sma_slow[-6:-3])) > 1.002
    long_flag = ((sma_slow[-2] < crypto_currency.close_values[-1] < np.mean(sma_slow[-2:])*1.01) and
                (np.mean(sma_slow[-3:]) > np.mean(sma_slow[-6:-2])) and
                (rsi < 60))

    #sma_short_diff = (np.mean(sma_slow[-3:]) / np.mean(sma_slow[-6:-3])) < 0.995
    short_flag = ((sma_slow[-2] > crypto_currency.close_values[-1] > np.mean(sma_slow[-2:])*0.99) and
                 (np.mean(sma_slow[-3:]) < np.mean(sma_slow[-6:-2])) and
                 (rsi > 40))

    crypto_currency.sma200 = sma_slow[-1]
    crypto_currency.sma40 = sma_fast[-1]
    crypto_currency.rsi = rsi
    return long_flag, short_flag

@error_wrapper
def get_order_book(crypto_currency, api):
    order_book = api.client.futures_orderbook_ticker(symbol=crypto_currency.symbol, requests_params={'timeout': 2})  # float(['askPrice']) - (mod * 0.01)

    ask_price = float(order_book['askPrice'])
    bid_price = float(order_book['bidPrice'])

    return ask_price, bid_price

@error_wrapper
def open_order(crypto_currency, price, api, limit_or_stop):

    params_L = {'symbol': crypto_currency.symbol,
                'side': 'BUY',
                'positionSide': 'LONG',
                'type': 'LIMIT',
                'quantity': crypto_currency.order_qty,
                'price': round(price, 2),
                'timeInForce': 'GTC',
                'recvWindow': 3000,
                'timestamp': int(time.time() * 1000)
                }

    stop_L_params = {'symbol': crypto_currency.symbol,
            'side': 'SELL',
            'positionSide': 'LONG',
            'type': 'STOP_MARKET',
            'stopPrice': round(price, 2),
            'quantity': crypto_currency.order_qty,
            'recvWindow': 3000,
            'priceProtect': 'true',
            'timestamp': int(time.time() * 1000)
            }

    params_S = {'symbol': crypto_currency.symbol,
            'side': 'SELL',
            'positionSide': 'SHORT',
            'type': 'LIMIT',
            'quantity': crypto_currency.order_qty,
            'price': round(price, 2),
            'timeInForce': 'GTC',
            'recvWindow': 3000,
            'timestamp': int(time.time() * 1000)
            }

    stop_S_params = {'symbol': crypto_currency.symbol,
            'side': 'BUY',
            'positionSide': 'SHORT',
            'type': 'STOP_MARKET',
            'stopPrice': round(price, 2),
            'quantity': crypto_currency.order_qty,
            'recvWindow': 3000,
            'priceProtect': 'true',
            'timestamp': int(time.time() * 1000)
            }

    if limit_or_stop == 'LONG':
        params = params_L
    elif limit_or_stop == 'STOP_LONG':
        params = stop_L_params
    elif limit_or_stop == 'SHORT':
        params = params_S
    elif limit_or_stop == 'STOP_SHORT':
        params = stop_S_params

    
    response = api.Futures_client.new_order(**params)
    crypto_currency.order_kline_time = crypto_currency.current_kline_time
    print('Open', limit_or_stop,
          'Symbol -', crypto_currency.symbol,
          'Price =', price)

    if (limit_or_stop == 'STOP_LONG') or (limit_or_stop == 'STOP_SHORT'):

        crypto_currency.stop_orders[limit_or_stop].append(response['orderId'])

    return response

@error_wrapper
def query_order(crypto_currency, orderId, api):
    response = api.Futures_client.query_order(**{'symbol': crypto_currency.symbol,
                                                      'orderId': orderId,
                                                      'timestamp': int(time.time() * 1000)})
    return response


@error_wrapper
def cancel_order(crypto_currency, orderId, api):
    api.Futures_client.cancel_order(**{'symbol': crypto_currency.symbol,
                                        'orderId': orderId,
                                        'timestamp': int(time.time() * 1000)})

def open_long_and_stop(crypto_currency, api):
    
    ask_price, bid_price = get_order_book(crypto_currency)

    long_response = open_order(crypto_currency, ask_price, api, "LONG")
    
    trigger_time = int(time.time())
    while (long_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 15):
        long_response = query_order(crypto_currency, long_response['orderId'], api)
        
    if long_response['status'] == 'FILLED':
        stop_long_response = open_order(crypto_currency, crypto_currency.sma200 - 0.05, api, "STOP_LONG") 

    else:
        cancel_order(crypto_currency, long_response['orderId'], api)

def open_short_and_stop(crypto_currency, api):
    ask_price, bid_price = get_order_book(crypto_currency)

    short_response = open_order(crypto_currency, bid_price, api, "SHORT")
    
    trigger_time = int(time.time())
    while (short_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 15):
        short_response = query_order(crypto_currency, short_response['orderId'], api)

    if short_response['status'] == 'FILLED':
        stop_short_response = open_order(crypto_currency, crypto_currency.sma200 + 0.05, api, "STOP_SHORT")

    else:
        cancel_order(crypto_currency, short_response['orderId'], api)
#################################################################################################
#################################################################################################
#################################################################################################

def get_stop_and_reopen(crypto_currency, api):
    for ordtype in crypto_currency.stop_orders:
        for id in crypto_currency.stop_orders[ordtype]:

            response = query_order(crypto_currency, id, api)
            is_new = response['status'] == 'NEW'

            if ((ordtype == 'STOP_LONG') and
                (float(response['stopPrice']) < crypto_currency.sma200) and
                is_new):

                if (crypto_currency.sma40 > crypto_currency.sma200) and (crypto_currency.close_values[-1] > crypto_currency.sma40*1.05) and (crypto_currency.rsi > 70):
                    stop_L_resp = open_order(crypto_currency, crypto_currency.sma40 - 0.05, api, 'STOP_LONG')
                else:
                    stop_L_resp = open_order(crypto_currency, crypto_currency.sma200 - 0.05, api, 'STOP_LONG')

                crypto_currency.stop_orders[ordtype].append(stop_L_resp['orderId'])
                
                cancel_order(crypto_currency, id, api)
                crypto_currency.stop_orders[ordtype].remove(id)
                

            elif ((ordtype == 'STOP_SHORT') and
                  (float(response['stopPrice']) > crypto_currency.sma200) and
                  is_new):

                if (crypto_currency.sma40 < crypto_currency.sma200) and (crypto_currency.close_values[-1] < crypto_currency.sma40*0.95) and (crypto_currency.rsi < 30):
                    stop_L_resp = open_order(crypto_currency, crypto_currency.sma40 + 0.05, api, 'STOP_SHORT')
                else:
                    stop_L_resp = open_order(crypto_currency, crypto_currency.sma200 + 0.05, api, 'STOP_SHORT')

                crypto_currency.stop_orders[ordtype].append(stop_L_resp['orderId'])
                
                cancel_order(crypto_currency, id, api)
                crypto_currency.stop_orders[ordtype].remove(id)
                

@error_wrapper
def get_position_info(crypto_currency, api):
    pos_response = api.client.futures_position_information(symbol=crypto_currency.symbol)[0]
    return pos_response

def check_open_positions(crypto_currency, max_amount: float, api):
    time.sleep(3)
    if crypto_currency.permitted_order_type != 'ANY':
        pos_response = get_position_info(crypto_currency, api)
        crypto_currency.active_pos_amount = float(pos_response['positionAmt'])
        if np.abs(crypto_currency.active_pos_amount) < max_amount:
            crypto_currency.permitted_order_type = "ANY"
        elif np.abs(crypto_currency.active_pos_amount) >= max_amount:
            crypto_currency.permitted_order_type = "MAX_SIZE"



def trade(crypto_currency, api):
    now_time = time.time()
    if (now_time - crypto_currency.prev_time) > 180:
        print(crypto_currency.symbol, '\n', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_time)))
        crypto_currency.prev_time = now_time

    api.get_crypto_currency_update(crypto_currency)

    long_flag, short_flag = get_conditions_to_open_order(crypto_currency)

    check_open_positions(crypto_currency, 0.02, api)

    
    if ((crypto_currency.current_kline_time - crypto_currency.order_kline_time) >= (60000*1)):  # More then *n minutes between orders

        match crypto_currency.permitted_order_type:
            case 'ANY':
                if long_flag:

                   open_long_and_stop(crypto_currency, api)

                elif short_flag:

                   open_short_and_stop(crypto_currency, api)

            case "MAX_SIZE":
                pass

        
        get_stop_and_reopen(crypto_currency, api)

@error_wrapper
def connect_to_api(public_key, private_key, Symbols, leverage):
    api = Binance()

    api.connect_to_api(public_key, private_key)

    server_time = api.client.get_server_time()
    gmtime=time.gmtime(int((server_time["serverTime"])/1000))
    win32api.SetSystemTime(gmtime[0],gmtime[1],0,gmtime[2],gmtime[3],gmtime[4],gmtime[5],0)

    for symbol in Symbols:
        api.Futures_client.change_leverage(symbol, leverage)

    return api


def get_CCs_historical(api, Symbols, Interval, Limit):

    Crypto_Currencies = []
    for symbol in Symbols:
        #print(symbol, Symbols[symbol])
        crypto_currency = CryptoCurrency(symbol=symbol, interval=Interval, limit=Limit, order_qty=Symbols[symbol])
        api.get_historical_data(crypto_currency)
        Crypto_Currencies.append(crypto_currency)

    return Crypto_Currencies
