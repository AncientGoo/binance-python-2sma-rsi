
from hashlib import shake_128
from views.api import API
from indicators.indicators import Indicators
from apikey import Keys
import time
import win32api
import winsound
import numpy as np
import websocket
import json
import pandas as pd


Symbol = 'BNBBUSD'
Interval = '1m'
Limit = 1000

min_interval = 1 # in minutes (for 1m candles)

min_sl = 0.0035
min_sl_activation = 0.0013
min_tp = 0.0026

leverage = 1 # 
margintype = 'ISOLATED'
order_qty = 0.02


stop_take_pairs = {}

limit_price_shift =  0.02

def open_small_long(crypto_currency, current_kline_time):
    
    while True:
        try:
            order_book = api.client.futures_orderbook_ticker(symbol=Symbol, requests_params={'timeout': 2})  # float(['askPrice']) - (mod * 0.01)

            ask_price = float(order_book['bidPrice']) - 0.02

            s1 = crypto_currency.low_values[-2] + (1/3)*(crypto_currency.close_values[-2] - crypto_currency.low_values[-2])
            s2 = crypto_currency.low_values[-3] + (1/3)*(crypto_currency.close_values[-3] - crypto_currency.low_values[-3])
            stop_price = np.mean([s1, s2])
            if crypto_currency.volume[-2] < np.mean(crypto_currency.volume[-5:-2]):
                stop_price -= 0.1
            break
        except Exception as ex:
            print(ex)
            print('Get long orderbook failed')
            time.sleep(0.25)
            pass


    
    params_L = {'symbol': Symbol,
                'side': 'BUY',
                'positionSide': 'LONG',
                'type': 'LIMIT',
                'quantity': order_qty,
                'price': round(ask_price, 2),
                'timeInForce': 'GTC',
                'recvWindow': 3000,
                'timestamp': int(time.time() * 1000)
                }


    while True:
        try:
            print('Open Long order')

            long_response = api.Futures_client.new_order(**params_L)

            
            break
        except Exception as ex:
            print(ex)
            print('Open hf order failed -> sleep(0.25)')
            time.sleep(0.25)
            pass

    
    trigger_time = int(time.time())
    while (long_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 15):
        # print((int(time.time()) - trigger_time))
        try:
            long_response = api.Futures_client.query_order(**{'symbol': Symbol,
                                                            'orderId': long_response['orderId'],
                                                            'timestamp': int(time.time() * 1000)})

        except Exception as ex:
            print(ex, '\nQuery main short order failed -> sleep(1)')
            time.sleep(1)
            pass

    if long_response['status'] == 'FILLED':
        crypto_currency.order_kline_time = current_kline_time

        stop_L_params = {'symbol': Symbol,
            'side': 'SELL',
            'positionSide': 'LONG',
            'type': 'STOP', #'STOP_MARKET',
            'stopPrice': str(round(stop_price, 2)),          # str(round(mark_price*(1-mod_a), 2))
            'price': str(round(stop_price+0.04, 2)),
            'quantity': str(order_qty),
            'timeInForce': 'GTC',
            'recvWindow': '3000',
            'priceProtect': 'TRUE',
            'timestamp': str(int(time.time() * 1000))
            }
            
        takeprofit_L_params = {'symbol': Symbol,
            'side': 'SELL',
            'positionSide': 'LONG',
            'type': 'LIMIT',
            'price': str(round(ask_price + (ask_price - stop_price), 2)),
            'quantity': str(order_qty),
            'timeInForce': 'GTC',
            'recvWindow': str(3000),
            'timestamp': str(int(time.time() * 1000))
            }
        print('Open stop loss market order')
        while True:
            try:
                stop_long_response, takeprofit_long_response = api.Futures_client.new_batch_order([stop_L_params, takeprofit_L_params])
                
                try:
                    stop_take_pairs[long_response['orderId']] = [stop_long_response['orderId'], takeprofit_long_response['orderId']]
                except:
                    pass
                print(stop_long_response,'\n', takeprofit_long_response)
                winsound.PlaySound(sound='SystemHand', flags=winsound.SND_ALIAS)

                print(stop_long_response, '\n', takeprofit_long_response)
                break

            except Exception as ex:
                print(ex)
                print('Open TP/SL long failed -> sleep(1)')
                time.sleep(1)
                # pass
        
    else:
        trigger_time = int(time.time())
        while (int(time.time()) - trigger_time < 5):
            try:
                api.Futures_client.cancel_order(**{'symbol': Symbol,
                                                'orderId': long_response['orderId'],
                                                'timestamp': int(time.time() * 1000)})
                break
            except:
                print('Cancel long order failed -> sleep(0.5)')
                time.sleep(1)
                pass

#################################################################################################
#################################################################################################
#################################################################################################

def open_small_short(crypto_currency, current_kline_time):
    
    while True:
        try:
            order_book = api.client.futures_orderbook_ticker(symbol=Symbol, requests_params={'timeout': 2})  # float(['askPrice']) - (mod * 0.01)

            bid_price = float(order_book['askPrice']) + 0.07

            s1 = crypto_currency.high_values[-2] - (1/3)*(crypto_currency.high_values[-2] - crypto_currency.close_values[-2])
            s2 = crypto_currency.high_values[-3] - (1/3)*(crypto_currency.high_values[-3] - crypto_currency.close_values[-3])
            stop_price = np.mean([s1, s2])

            if crypto_currency.volume[-2] < np.mean(crypto_currency.volume[-5:-2]):
                stop_price += 0.02
            break

        except Exception as ex:
            print(ex)
            print('Get short orderbook failed')
            time.sleep(0.25)
            pass


    
    params_S = {'symbol': Symbol,
                'side': 'SELL',
                'positionSide': 'SHORT',
                'type': 'LIMIT',
                'quantity': order_qty,
                'price': round(bid_price, 2),
                'timeInForce': 'GTC',
                'recvWindow': 3000,
                'timestamp': int(time.time() * 1000)
                }


    while True:
        try:
            print('Open Short order')

            short_response = api.Futures_client.new_order(**params_S)

            crypto_currency.order_kline_time = current_kline_time
            break
        except Exception as ex:
            print(ex)
            print('Open hf order failed -> sleep(0.25)')
            time.sleep(0.25)
            pass

    
    trigger_time = int(time.time())
    while (short_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 15):
        # print((int(time.time()) - trigger_time))
        try:
            short_response = api.Futures_client.query_order(**{'symbol': Symbol,
                                                            'orderId': short_response['orderId'],
                                                            'timestamp': int(time.time() * 1000)})

        except Exception as ex:
            print(ex, '\nQuery main short order failed -> sleep(1)')
            time.sleep(1)
            pass

    if short_response['status'] == 'FILLED':
        crypto_currency.order_kline_time = current_kline_time

        stop_S_params = {
            'symbol': Symbol,
            'side': 'BUY',  #'BUY',
            'positionSide': 'SHORT',
            'type': 'STOP', # 'STOP_MARKET',
            'stopPrice': str(round(stop_price, 2)),
            'price': str(round(stop_price - 0.04, 2)),
            'quantity': str(order_qty),
            'timeInForce': 'GTC',
            'recvWindow': '3000',
            'timestamp': str(int(time.time() * 1000)),
            #'reduceOnly': 'false'
            }
        takeprofit_S_params = {
            'symbol': Symbol,
            'side': 'BUY',
            'positionSide': 'SHORT',
            'type': 'LIMIT',
            'price': str(round(bid_price - (stop_price - bid_price), 2)),
            'quantity': str(order_qty),
            'timeInForce': 'GTC',
            'recvWindow': str(3000),
            'timestamp': str(int(time.time() * 1000))
            }
        print('Open stop loss market order')
        while True:
            try:
                stop_short_response, takeprofit_short_response = api.Futures_client.new_batch_order([stop_S_params, takeprofit_S_params])
                try:
                    stop_take_pairs[short_response['orderId']] = [stop_short_response['orderId'], takeprofit_short_response['orderId']]
                except:
                    pass
                winsound.PlaySound(sound='SystemHand', flags=winsound.SND_ALIAS)

                print(stop_short_response, '\n', takeprofit_short_response)
                break

            except Exception as ex:
                print(ex)
                print('Open TP/SL long failed -> sleep(1)')
                time.sleep(1)
                # pass
        
    else:
        trigger_time = int(time.time())
        while (int(time.time()) - trigger_time < 5):
            try:
                api.Futures_client.cancel_order(**{'symbol': Symbol,
                                                'orderId': short_response['orderId'],
                                                'timestamp': int(time.time() * 1000)})
                break
            except:
                print('Cancel long order failed -> sleep(0.5)')
                time.sleep(1)
                pass

#################################################################################################
#################################################################################################
#################################################################################################


def open_long(crypto_currency, current_kline_time, mod_02, mod_03, mod_a):
    
    trigger_time = int(time.time())
    

    while True:
        try:
            # mark_price = float(api.Futures_client.mark_price(Symbol)["markPrice"])  - limit_price_shift
            mark_price = float(api.client.futures_orderbook_ticker(symbol=Symbol, requests_params={'timeout': 3})['askPrice']) - limit_price_shift

            # crypto_currency.order_kline_time = current_kline_time
            break
        except:
            print('Get orderbook failed -> sleep(0.5)')
            time.sleep(1)
            pass


    
    long_params = {'symbol': Symbol,
                'side': 'BUY',
                'positionSide': 'LONG',
                'type': 'LIMIT', # 'MARKET',
                'quantity': order_qty,
                'price': round(mark_price, 2),
                'timeInForce': 'GTC',
                'recvWindow': 3000,
                'timestamp': int(time.time() * 1000)
                }

    while True:
        try:
            print('Open long order')
            long_response = api.Futures_client.new_order(**long_params)
            print(long_response)
            time.sleep(1)
            break
        except Exception as ex:
            print(ex)
            print('\nOpen main short order failed -> sleep(0.5)')
            time.sleep(1)
            pass


    while (long_response['status'] != 'FILLED') and ((int(time.time()) - trigger_time) < 15):
        # print((int(time.time()) - trigger_time))
        try:
            long_response = api.Futures_client.query_order(**{'symbol': Symbol,
                                                            'orderId': long_response['orderId'],
                                                            'timestamp': int(time.time() * 1000)})
            time.sleep(0.5)
        except Exception as ex:
            print(ex, '\nQuery main short order failed -> sleep(1)')
            time.sleep(1)
            pass

    

    if long_response['status'] == 'FILLED':
        crypto_currency.order_kline_time = current_kline_time
        print('Open stop loss market order')
        stop_long_params = {'symbol': Symbol,
                    'side': 'SELL',
                    'positionSide': 'LONG',
                    'type': 'STOP', #'STOP_MARKET',
                    'stopPrice': str(round(mark_price*(1-mod_02), 2)),          # str(round(mark_price*(1-mod_a), 2))
                    'price': str(round(mark_price*(1-mod_02), 2)),
                    'quantity': str(order_qty),
                    'timeInForce': 'GTC',
                    'recvWindow': '3000',
                    'priceProtect': 'TRUE',
                    'timestamp': str(int(time.time() * 1000))
                    }

        print('Open take profit market order')
        takeprofit_long_params = {'symbol': Symbol,
                    'side': 'SELL',
                    'positionSide': 'LONG',
                    'type': 'LIMIT',
                    'price': str(round(mark_price*(1+mod_03), 2)),
                    'quantity': str(order_qty),
                    'timeInForce': 'GTC',
                    'recvWindow': '3000',
                    'timestamp': str(int(time.time() * 1000))
                    }
        while True:
            try:
                stop_long_response, takeprofit_long_response = api.Futures_client.new_batch_order([stop_long_params, takeprofit_long_params])

                stop_take_pairs[long_response['orderId']] = [stop_long_response['orderId'], takeprofit_long_response['orderId']]
                winsound.PlaySound(sound='SystemHand', flags=winsound.SND_ALIAS)
                #crypto_currency.last_open_orders_id.append(long_response['orderId'])
                ####### crypto_currency.last_open_order_type = 'LONG'
                print(stop_long_response, takeprofit_long_response)
                break

            except Exception as ex:
                print(ex)
                print('Open TP/SL long failed -> sleep(1)')
                time.sleep(1)
                # pass
    
    else:
        trigger_time = int(time.time())
        while (int(time.time()) - trigger_time < 5):
            try:
                api.Futures_client.cancel_order(**{'symbol': Symbol,
                                                'orderId': long_response['orderId'],
                                                'timestamp': int(time.time() * 1000)})
                break
            except:
                print('Cancel long order failed -> sleep(0.5)')
                time.sleep(1)
                pass

def open_short(crypto_currency, current_kline_time, mod_02, mod_03, mod_a):
    
    

    # mark_price = float(api.client.futures_orderbook_ticker(symbol=Symbol, requests_params={'timeout': 3})['bidPrice']) + limit_price_shift
    trigger_time = int(time.time())

    

    while True:
        try:
            # mark_price = float(api.Futures_client.mark_price(Symbol)["markPrice"]) + limit_price_shift
            mark_price = float(api.client.futures_orderbook_ticker(symbol=Symbol, requests_params={'timeout': 3})['bidPrice']) + limit_price_shift

            # crypto_currency.order_kline_time = current_kline_time
            break
        except:
            print('Get orderbook failed -> sleep(0.5)')
            time.sleep(1)
            pass

    
    short_params = {'symbol': Symbol,
                    'side': 'SELL', #'SELL',
                    'positionSide': 'SHORT',
                    'type': 'LIMIT', #'MARKET',
                    'quantity': order_qty,
                    'price': round(mark_price, 2),
                    'timeInForce': 'GTC',
                    'recvWindow': 3000,
                    'timestamp': int(time.time() * 1000),
                    #'reduceOnly': 'false'
                }
    
    
    while True:
        try:
            print('Open short order')
            short_response = api.Futures_client.new_order(**short_params)
            print(short_response)
            time.sleep(1)
            break
        except Exception as ex:
            print(ex)
            print('Open main short order failed -> sleep(1)')
            time.sleep(1)
            pass

    

    while (short_response['status'] != 'FILLED') and (short_response['status'] != 'PLACED') and ((int(time.time()) - trigger_time) < 15):
        # print((int(time.time()) - trigger_time))
        try:
            short_response = api.Futures_client.query_order(**{'symbol': Symbol,
                                                            'orderId': short_response['orderId'],
                                                            'timestamp': int(time.time() * 1000)})
            time.sleep(0.5)
        except Exception as ex:
            print(ex, '\nQuery main short order failed -> sleep(1)')
            time.sleep(1)
            pass

    if short_response['status'] == 'FILLED':
        crypto_currency.order_kline_time = current_kline_time
        print('Main short Filled')
        print('Open stop loss order')
        stop_short_params = {'symbol': Symbol,
                    'side': 'BUY',  #'BUY',
                    'positionSide': 'SHORT',
                    'type': 'STOP', # 'STOP_MARKET',
                    'stopPrice': str(round(mark_price*(1 + mod_02), 2)),
                    'price': str(round(mark_price*(1 + mod_02), 2)),
                    'quantity': str(order_qty),
                    'timeInForce': 'GTC',
                    'recvWindow': '3000',
                    'timestamp': str(int(time.time() * 1000)),
                    #'reduceOnly': 'false'
                    }

        print('Open take profit market order')
        takeprofit_short_params = {'symbol': Symbol,
                    'side': 'BUY',
                    'positionSide': 'SHORT',
                    'type': 'LIMIT',
                    'price':str(round(mark_price*(1-mod_03)-0.05, 2)),
                    'quantity': str(order_qty),
                    'timeInForce': 'GTC',
                    'recvWindow': '3000',
                    'priceProtect': 'TRUE',
                    'timestamp': str(int(time.time() * 1000)),
                    #'reduceOnly': 'false'
                    }
        while True:
            try:
                stop_short_response, takeprofit_short_response = api.Futures_client.new_batch_order([stop_short_params, takeprofit_short_params])

                stop_take_pairs[short_response['orderId']] = [stop_short_response['orderId'], takeprofit_short_response['orderId']]
                winsound.PlaySound(sound='SystemHand', flags=winsound.SND_ALIAS)
                #crypto_currency.last_open_orders_id.append(short_response['orderId'])
                ###### crypto_currency.last_open_order_type = 'SHORT'
                print(stop_short_response,'/n', takeprofit_short_response)

                break
                
            except Exception as ex:
                print(ex)
                print('Open TP/SL short failed -> sleep(1)')
                time.sleep(1)
                # pass

    else:
        trigger_time = int(time.time())
        while (int(time.time()) - trigger_time < 5):
            try:
                api.Futures_client.cancel_order(**{'symbol': Symbol,
                                                'orderId': short_response['orderId'],
                                                'timestamp': int(time.time() * 1000)})

                break
            except:
                print('Cancel short order failed -> sleep(0.5)')
                time.sleep(1)
                pass

def trade(new_kline, crypto_currency):
    now_time = time.time()
    if (now_time - crypto_currency.prev_time) > 55:
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_time)))
        crypto_currency.prev_time = now_time
    # try:
    # Taking Crypto Currency Values
    # crypto_currency, current_kline_time = api.get_crypto_currency_update(new_kline)
    current_kline_time = api.get_crypto_currency_update(new_kline)
    # Calc indicators
    rsi = Indicators.RSI(crypto_currency).values
    #roc_arr = Indicators.ROC(crypto_currency, w=60)
    #roc = roc_arr[-1]
    #sma = Indicators.SMA(crypto_currency, w=180).iloc[-1]
    #dpo = Indicators.DPO(crypto_currency, w=6)
    #print(dpo[-5:])
    macd = Indicators.MACD(crypto_currency)[-3:]

    #is_dpo_high = np.mean(dpo[-2:]) > np.mean(dpo[-3:-1])
    #is_dpo_low = np.mean(dpo[-2:]) < np.mean(dpo[-3:-1])
    #is_roc_high = (np.mean(roc_arr[-3:]) > roc_arr[-4]) and (roc > -0.15)
    #is_roc_low = (np.mean(roc_arr[-3:]) < roc_arr[-4]) and (roc < 0.15)
    is_macd_long = (np.mean(macd[-2:]) > np.mean(macd[-3:-1])) and (rsi[-1] > np.mean(rsi[-4:-1])) and (rsi[-1] < 60) # (macd[-1] > 0.035) and 
    is_macd_short = (macd[-1] < -0.035) and (np.mean(macd[-2:]) < np.mean(macd[-3:-1])) and (rsi[-1] < np.mean(rsi[-4:-1])) and (rsi[-1] > 40) # (macd[-1] < -0.035) and 
    # Set flag (allow to open order)
    #price_corridor_flag = (sma*0.9987 < crypto_currency.close_values[-1] < sma*1.0013)

    mod_02 = min_sl
    mod_03 = min_tp
    mod_a = min_sl_activation
    # if vol_frac < 0.2:
    #     mod_02 *= 0.6
    #     mod_03 *= 0.6


    def common_trade():            
        #################
        if ((current_kline_time - crypto_currency.order_kline_time) >= (60000*min_interval)):  # More then *n minutes betwee orders
            # print(f'>{min_interval} minutes since the last order')

            match crypto_currency.last_open_order_type:
                case 'ANY':
                    ### Trade both side
                    if is_macd_long: #(48 < rsi < 52) and (-0.15 < roc < 0.15) and is_dpo_greater:
                        #Long
                        open_small_long(crypto_currency, current_kline_time)
                        pass
                   # elif is_macd_short: #(48 < rsi < 52) and (-0.15 < roc < 0.15) and (not is_dpo_greater):
                        #Short
                        # open_small_short(crypto_currency, current_kline_time)     
                   #     pass    

                case "MAX_SIZE":
                    pass


            if crypto_currency.last_open_order_type != 'ANY':
                pos_response = api.client.futures_position_information(symbol=Symbol)[0]
                crypto_currency.active_pos_amount = float(pos_response['positionAmt'])
                if np.abs(crypto_currency.active_pos_amount) < 0.04:
                    crypto_currency.last_open_order_type = "ANY"
                elif np.abs(crypto_currency.active_pos_amount) >= 0.04:
                    crypto_currency.last_open_order_type = "MAX_SIZE"
            
    match crypto_currency.next_mode:
        case "COMMON":
            # crypto_currency.next_mode = "HF"
            common_trade()
            
        #case "HF":
        #    crypto_currency.next_mode = "COMMON"
        #    hf_trade()
            

    ####### Cancel orders ###########
    # print('Cancel orders')
    rm_keys = set()
    for main_order_id in stop_take_pairs:

        stop_loss_params = {'symbol': Symbol,
                            'orderId':  str(stop_take_pairs[main_order_id][0]),
                            'timestamp': int(time.time() * 1000)
                            }

        take_profit_params = {'symbol': Symbol,
                            'orderId':  str(stop_take_pairs[main_order_id][1]),
                            'timestamp': int(time.time() * 1000)
                            }
        
        try:
            r1_resp = api.Futures_client.query_order(**take_profit_params)
            r1 = r1_resp['status']
        except:
            print('TP get order error')
            r1 = 0
            pass

        if r1 == 'FILLED':
 
            print('No TP, cancel SL')
            cancel_params = {'symbol': Symbol,
                            'orderId':  str(stop_take_pairs[main_order_id][0]),
                            'timestamp': int(time.time() * 1000)
                            }
            try:
                api.Futures_client.cancel_order(**cancel_params)
            except:
                print('SL cancelling error')
                pass
            
            rm_keys.add(main_order_id)
        else:
            try:
                r0_resp = api.Futures_client.query_order(**stop_loss_params)
                r0 = r0_resp['status']
            except Exception as ex:
                print('SL get order error')
                r0 = 0
                pass

            if r0 == 'FILLED':
                print('No SL, cancel TP')
                cancel_params = {'symbol': Symbol,
                                'orderId':  str(stop_take_pairs[main_order_id][1]),
                                'timestamp': int(time.time() * 1000)
                                }
                try:
                     api.Futures_client.cancel_order(**cancel_params)
                except:
                    print('TP cancelling error')
                    pass
                
                rm_keys.add(main_order_id)

        

    for key in rm_keys:
        stop_take_pairs.pop(key)

    # if stop_take_pairs == {}:
    #    crypto_currency.order_kline_time = 0

    # crypto_currency.prev_dpo = dpo[-1]
    #time.sleep(0.8)
    #print('Next iteration')


def set_websocket_and_trade(Symbol, Interval, crypto_currency):
    socket = f'wss://fstream.binance.com/ws/{Symbol.lower()}@kline_{Interval}'

    def on_message(ws, message):
        json_msg = json.loads(message)
        candle = json_msg['k']
        new_kline = [[candle['t'],
                     candle['o'],
                     candle['h'],
                     candle['l'],
                     candle['c'],
                     candle['v'] 
                    ]]
        trade(new_kline, crypto_currency)
        # print('New iteration')



    def on_close(ws, *args):
        print(args)
        print('### ws close ###')

    ws = websocket.WebSocketApp(socket, on_message=on_message, on_close=on_close)
    ws.run_forever()



if __name__ == "__main__":
    # Connect to API
    api = API()
    while True:
        try:
            # Futures_client = Futures(Keys.public, Keys.private) 
            api.connect_to_api(Keys.public,
                               Keys.private)

            server_time = api.client.get_server_time()
            gmtime=time.gmtime(int((server_time["serverTime"])/1000))
            win32api.SetSystemTime(gmtime[0],gmtime[1],0,gmtime[2],gmtime[3],gmtime[4],gmtime[5],0)

            crypto_currency = api.get_historical_data(Symbol, Interval, Limit)
            
            ### Set leverage!!!!!! ######
            api.Futures_client.change_leverage(Symbol, leverage)
            ### Change margin type ######
            #try:
            #    api.Futures_client.change_margin_type(Symbol, marginType=margintype)
            #except:
            #    pass
            ################################
            set_websocket_and_trade(Symbol, Interval, crypto_currency)  
            break
        except Exception as ex:
           print(ex.args)
           print('Connection error, sleep 10 seconds')
           time.sleep(10)
           pass

                  




