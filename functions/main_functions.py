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
                resp = func(*args)
                return resp

            except Exception as ex:
                if ex.args[2] == "Order does not exist.":
                    return ex.args[2]
                print(ex)
                print('Error in', str(func))
                time.sleep(5)
                if time.time()-trigger_time > 30:
                    break
                else:
                    pass


    return wrapper



def get_conditions_to_open_order(crypto_currency):
    sma_slow = Indicators.SMA(crypto_currency, w=200).iloc[-2:].values
    sma_fast = Indicators.SMA(crypto_currency, w=40).iloc[-2:].values


    rsi = Indicators.RSI(crypto_currency).iloc[-1]


    long_flag = ((sma_slow[-1] < crypto_currency.close_values[-1] < sma_slow[-1]*1.01) and
                (sma_fast[-1] > sma_slow[-1]) and
                (rsi < 60))
                #or
                #(crypto_currency.close_values[-2] > sma_slow[-1]) and
                #(crypto_currency.close_values[-1] < sma_slow[-1]*1.01))

    short_flag = ((sma_slow[-1] > crypto_currency.close_values[-1] > sma_slow[-1]*0.99) and
                 (sma_fast[-1] < sma_slow[-1]) and
                 (rsi > 40))
                 #or
                 #(crypto_currency.close_values[-2] < sma_slow[-1]) and 
                 #(crypto_currency.close_values[-1] > sma_slow[-1]*0.99))

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
def open_order(crypto_currency, price, api, limit_or_stop, new_or_not='NEW'):

    params_L = {'symbol': crypto_currency.symbol,
                'side': 'BUY',
                'positionSide': 'LONG',
                'type': 'LIMIT',
                'quantity': crypto_currency.order_qty,
                'price': round(price, crypto_currency.precision),
                'timeInForce': 'GTC',
                'recvWindow': 3000,
                'timestamp': int(time.time() * 1000)
                }

    stop_L_params = {'symbol': crypto_currency.symbol,
            'side': 'SELL',
            'positionSide': 'LONG',
            'type': 'STOP_MARKET',
            'stopPrice': round(price, crypto_currency.precision),
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
            'price': round(price, crypto_currency.precision),
            'timeInForce': 'GTC',
            'recvWindow': 3000,
            'timestamp': int(time.time() * 1000)
            }

    stop_S_params = {'symbol': crypto_currency.symbol,
            'side': 'BUY',
            'positionSide': 'SHORT',
            'type': 'STOP_MARKET',
            'stopPrice': round(price, crypto_currency.precision),
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

    print(response, '\n')
    if (new_or_not == 'NEW') and ((limit_or_stop == 'STOP_LONG') or (limit_or_stop == 'STOP_SHORT')):
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
    
    ask_price, bid_price = get_order_book(crypto_currency, api) # ['askPrice']

    if ask_price <= crypto_currency.sma200*1.01:
        price = ask_price
    else:
        price = crypto_currency.sma200*1.01
    
    long_response = open_order(crypto_currency, price, api, "LONG")
    

    trigger_time = int(time.time())
    while (long_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 30):
        long_response = query_order(crypto_currency, long_response['orderId'], api)    
    
    
    if long_response['status'] == 'FILLED':
        time.sleep(2)
        stop_long_response = open_order(crypto_currency, crypto_currency.sma200*0.995, api, "STOP_LONG")
        #crypto_currency.active_pos_amount += crypto_currency.order_qty

        #time.sleep(3)
        
    else:
        cancel_order(crypto_currency, long_response['orderId'], api)

    

def open_short_and_stop(crypto_currency, api):
    ask_price, bid_price = get_order_book(crypto_currency, api)
    if bid_price >= crypto_currency.sma200*0.99:
        price = bid_price
    else:
        price = crypto_currency.sma200*0.99

    short_response = open_order(crypto_currency, price, api, "SHORT")
    
    trigger_time = int(time.time())
    while (short_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 30):
        short_response = query_order(crypto_currency, short_response['orderId'], api)
    

    if short_response['status'] == 'FILLED':
        time.sleep(2)
        stop_short_response = open_order(crypto_currency, crypto_currency.sma200*1.005, api, "STOP_SHORT")
        #crypto_currency.active_pos_amount += crypto_currency.order_qty
        #time.sleep(3)
            
    else:
        cancel_order(crypto_currency, short_response['orderId'], api)

#################################################################################################
#################################################################################################
#################################################################################################

def get_stop_and_reopen(crypto_currency, api):

    rm_list = {'STOP_LONG': [],
                'STOP_SHORT': []}
    app_list = {'STOP_LONG': [],
                'STOP_SHORT': []}

    now_time = time.time()
    if ((now_time-crypto_currency.prev_time) >= 60*15):

        print(crypto_currency.symbol, '     ',
              time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '     ',
              "sma40/sma200", round(crypto_currency.sma40/crypto_currency.sma200, 3), '     ',
              round(crypto_currency.sma200, 3), round(crypto_currency.sma40, 3), '     ', end = "\r")

        crypto_currency.prev_time = now_time

        #print('Reopen stops')
        for ordtype in crypto_currency.stop_orders:
            
            for id in crypto_currency.stop_orders[ordtype]:
                # print('\n', crypto_currency.stop_orders)

                response = query_order(crypto_currency, id, api)
                if response == 'Order does not exist.':
                    rm_list[ordtype].append(id)
                else:
                    is_new = (response['status'] == 'NEW')

                    if ((ordtype == 'STOP_LONG') and
                        (float(response['stopPrice']) < crypto_currency.sma200*0.995) and
                        is_new):

                        cancel_order(crypto_currency, id, api)
                        rm_list['STOP_LONG'].append(id)
                        time.sleep(1)
                        
                        print('New stop')
                        if (crypto_currency.sma40 > crypto_currency.sma200) and (crypto_currency.close_values[-1] > crypto_currency.sma40) and (crypto_currency.rsi > 55):
                            stop_resp = open_order(crypto_currency, crypto_currency.sma40*0.995, api, 'STOP_LONG', 'NOT')
                        else:
                            stop_resp = open_order(crypto_currency, crypto_currency.sma200*0.995, api, 'STOP_LONG', 'NOT')

                        app_list['STOP_LONG'].append(stop_resp['orderId'])
                        


                    elif ((ordtype == 'STOP_SHORT') and
                        (float(response['stopPrice']) > crypto_currency.sma200*1.005) and
                        is_new):

                        cancel_order(crypto_currency, id, api)
                        rm_list['STOP_SHORT'].append(id)
                        time.sleep(1)
                        
                        print('New stop')
                        if (crypto_currency.sma40 < crypto_currency.sma200) and (crypto_currency.close_values[-1] < crypto_currency.sma40) and (crypto_currency.rsi < 45):
                            stop_resp = open_order(crypto_currency, crypto_currency.sma40*1.005, api, 'STOP_SHORT', 'NOT')
                        else:
                            stop_resp = open_order(crypto_currency, crypto_currency.sma200*1.005, api, 'STOP_SHORT', 'NOT')

                        app_list['STOP_SHORT'].append(stop_resp['orderId'])
                

    for key in rm_list:
        for id in rm_list[key]:           
            crypto_currency.stop_orders[key].remove(id)
            crypto_currency.active_pos_amount -= crypto_currency.order_qty

    for key in app_list:
        for id in app_list[key]:            
            crypto_currency.stop_orders[key].append(id)
            crypto_currency.active_pos_amount += crypto_currency.order_qty

    

                
                
                

@error_wrapper
def get_position_info(crypto_currency, api):
    pos_response = api.client.futures_position_information(symbol=crypto_currency.symbol)[0]
    return pos_response

def check_open_positions(crypto_currency, mult: float, api):
    max_amount = crypto_currency.order_qty * mult

    if crypto_currency.active_pos_amount >= max_amount:
        crypto_currency.permitted_order_type = "MAX_SIZE"
    else:
        crypto_currency.permitted_order_type = "ANY"

    # if crypto_currency.permitted_order_type != 'ANY':
    #     pos_response = get_position_info(crypto_currency, api)
    #     crypto_currency.active_pos_amount = float(pos_response['positionAmt'])
    #     if np.abs(crypto_currency.active_pos_amount) < max_amount*0.9:
    #         crypto_currency.permitted_order_type = "ANY"
    #     elif np.abs(crypto_currency.active_pos_amount) >= max_amount*0.9:
    #         crypto_currency.permitted_order_type = "MAX_SIZE"

    #     print('Check_open_positions', pos_response)



def trade(crypto_currency, api):

    #now_time = time.time()
    #if (now_time - crypto_currency.prev_time) > 1800:
    #    print(crypto_currency.symbol, '\n', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_time)))
        

    api.get_crypto_currency_update(crypto_currency)
    
    

    if ((crypto_currency.current_kline_time - crypto_currency.order_kline_time) >= (60000*30)):  # More then *n minutes between orders
        

        long_flag, short_flag = get_conditions_to_open_order(crypto_currency)
        check_open_positions(crypto_currency, 1, api)

        match crypto_currency.permitted_order_type:
            case 'ANY':
                if long_flag:
                    print(crypto_currency.symbol, 'Long flag == True')
                    print("sma40/sma200 [-2]", round(crypto_currency.sma40/crypto_currency.sma200, 2))
                    open_long_and_stop(crypto_currency, api)

                elif short_flag:
                    print(crypto_currency.symbol, 'Short flag == True')
                    print("sma40/sma200 [-2]", round(crypto_currency.sma40/crypto_currency.sma200, 2))
                    open_short_and_stop(crypto_currency, api)

            case "MAX_SIZE":
                print("MAX_SIZE, active position amount =", crypto_currency.active_pos_amount)
                pass

        long_flag, short_flag = False, False

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
        crypto_currency = CryptoCurrency(symbol=symbol, interval=Interval, limit=Limit, order_qty=Symbols[symbol][0], precision=Symbols[symbol][1])
        api.get_historical_data(crypto_currency)
        Crypto_Currencies.append(crypto_currency)

    return Crypto_Currencies
