import numpy
import talib
import pandas
from ta.momentum import RSIIndicator as RSI
from ta.momentum import PercentageVolumeOscillator as PVO
from ta.trend import SMAIndicator as SMA
from ta.trend import EMAIndicator as EMA
from ta.volatility import BollingerBands as BB

class Indicator:
    def __init__(self):
        print("indicator created")
        self.data = None
        self.diamond = []
        self.golden = []
        self.silver = []
        self.copper = []
        self.rsi15m_list=[]

    def set_data(self, _data):
        self.data = pandas.Series(_data)

    def rsi(self, timeperiod=14):
        #ta.momentum.RSIIndicator(close: pandas.core.series.Series, window: int = 14, fillna: bool = False)
        return list(RSI(self.data, timeperiod, False).rsi())
         

    def ema(self, timeperiod):
        #ta.trend.ema_indicator(close, window=12, fillna=False)
        return list(EMA(self.data, window=timeperiod).ema_indicator())
    
    def pvo(self, short, long):
        #(volume: pandas.core.series.Series, window_slow: int = 26, window_fast: int = 12, window_sign: int = 9, fillna: bool = False)
        return list(PVO(self.data, long, short, 9).pvo())
         

    def bbands(self):
        #ta.volatility.BollingerBands(close: pandas.core.series.Series, window: int = 20, window_dev: int = 2, fillna: bool = False)
        bbands = BB(self.data)
        hband = bbands.bollinger_hband()
        hband_indicator = bbands.bollinger_hband_indicator()
        lband = bbands.bollinger_lband()
        lband_indicator = bbands.bollinger_lband_indicator()
        mavg = bbands.bollinger_mavg()

        return {
            "hband": list(hband),
            "hband_indicator": list(hband_indicator),
            "lband": list(lband),
            "lband_indicator": list(lband_indicator),
            "mavg": list(mavg)
        }
    
    def ma(self, timeperiod = 14):
        #ta.trend.SMAIndicator(close: pandas.core.series.Series, window: int, fillna: bool = False)
        return list(SMA(self.data, timeperiod).sma_indicator())

if __name__ == "__main__":
    data = [1,2,3,4,5,6,7,8,9,10,11,10,9,8,7,8,9,10,11,10,12,22,23,24,24,12,25,23,14,23,71,45,23,7]
    
    a = Indicator()
    a.set_data(data)
    _data = a.pvo(short=14, long=28)
    print(_data)