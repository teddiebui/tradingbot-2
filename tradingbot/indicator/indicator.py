import talib
import numpy
import pprint

class Indicator():

    def __init__(self, oversold_threshold = 30, overbought_threshold = 70):
        #rsi indicator variables
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.macd_threshold = 2.0
        self.rsi = []

        #macd indicator variables
        self.macd = []
        self.macd_signal = []
        self.macd_hist = []

        #ema
        self.ema_200 = []

        #dmi
        self.adx = []
        self.plus_di = []
        self.minus_di = []

        print("...indicator created")

    def update(self, candles):

        closes = [i['close'] for i in candles]

        self.refresh_rsi(closes)
        self.refresh_macd(closes)
        self.refresh_ema_200(closes)
        self.refresh_dmi(candles)

        #DEBUG
        # print()
        # print("rsi: ", self.rsi[-4:])
        # print()
        # print("macd: ", self.macd[-4:])   
        # print("macd signal: ", self.macd_signal[-4:]) 
        # print("macd histogram: ", self.macd_hist[-4:])    
        # print()
        # print("ema 200: ", self.ema_200[-4:]) 
        # print()
        # print("adx: ", self.adx[-4:])
        # print("+di: ", self.plus_di[-4:])
        # print("-di: ", self.minus_di[-4:])
        # print()
        # print("---------------------")


    def refresh_rsi(self, close_list):

        # CALCULATE by callback function _refresh_indicator
        try:
            rsi = talib.RSI(numpy.array(close_list))
            self.rsi = rsi[:]
        except Exception as e:
            pprint.pprint("...refresh_rsi..: ", e)

    def refresh_macd(self, close_list):

        # CALCULATE by callback function _refresh_indicator
        self.macd, self.macd_signal, self.macd_hist = talib.MACD(
            numpy.array(close_list),
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9)

    def refresh_ema_200(self, close_list):

        # CALCULATE by callback function _refresh_indicator
        self.ema_200 = talib.EMA(numpy.array(close_list),200)

    def refresh_dmi(self, candles):

        # CALCULATE by callback function _refresh_indicator

        high = []
        low = []
        close = []

        for i in candles:
            high.append(i['high'])
            low.append(i['low'])
            close.append(i['close'])

        self.adx = talib.ADX(high, low, close, 14)
        self.plus_di = talib.PLUS_DI(high, low, close,14)
        self.minus_di = talib.MINUS_DI(high, low, close,14)

    def validate_rsi(self, candles):
        #TODO: write code that check if rsi satisfy buying condition

        self.refresh_rsi([i['close'] for i in candles])

        if self.rsi[-1] < self.oversold_threshold:
            return True, self.rsi[-1]
        
        return False, self.rsi[-1]
    
    def validate_macd(self, candles):
        #TODO: write code that check if macd satisfy buying condition

        self.refresh_macd([i['close'] for i in candles])

        if len(self.macd) < 26:
            return False

        if self.macd[-2] >= -2 or self.macd_signal[-2] >= -2: #filter
            return False
            
        if self.macd[-1] >= -2 or self.macd_signal[-1] >= -2: #filter
            return False

        a = self.macd[-2] < self.macd[-1]
        b = self.macd[-2] < self.macd_signal[-1]

        return (self.macd[-2] < self.macd[-1]) and (self.macd[-2] < self.macd_signal[-1])

        # cross_over = (self.macd[-2] < self.macd_signal[-2]) and (self.macd[-1] > self.macd_signal[-1])
        # return cross_over

    def validate_ema(self, candles):
        #TODO: write code that check if ema satisfy buying condition
        self.refresh_ema_200([i['close'] for i in candles])

        return False

    def validate_dmi(self, candles):

        self.refresh_dmi(candles)
        #TODO: write code that check if dmi satisfy buying condition
        return False
    
    def get_config(self):
        return {
            'overSoldThreshold': self.oversold_threshold,
            'overBoughtThreshold': self.overbought_threshold
        }

if __name__ == "__main__":
    pass