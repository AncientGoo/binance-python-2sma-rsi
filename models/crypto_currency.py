class CryptoCurrency:
    next_mode = "COMMON"
    active_pos_amount = 0
    last_open_order_type = 'ANY'
    prev_dpo = None
    order_kline_time = 0
    prev_time = 0

    def __init__(self, symbol, interval, limit):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

        self.open_time = [None] * self.limit
        self.open_values = [None] * self.limit
        self.close_values = [None] * self.limit
        self.high_values = [None] * self.limit
        self.low_values = [None] * self.limit
        self.volume = [None] * self.limit


