import time

class CryptoCurrency:
    prev_time = 0
    active_pos_amount = 0
    permitted_order_type = 'ANY'
    prev_dpo = None
    order_kline_time = 0
    current_kline_time = 0

    stop_orders = {'STOP_LONG': [],
                   'STOP_SHORT': []}

    sma200 = 1
    sma40 = 1
    rsi = 50

    # sma_fast = None

    def __init__(self, symbol, interval, limit, order_qty, precision):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.order_qty = order_qty
        self.precision = precision

        self.open_time = [None] * self.limit
        self.open_values = [None] * self.limit
        self.close_values = [None] * self.limit
        self.high_values = [None] * self.limit
        self.low_values = [None] * self.limit
        self.volume = [None] * self.limit
        

        #self.prev_time = time.time()
