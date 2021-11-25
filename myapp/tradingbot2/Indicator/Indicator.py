import numpy
import talib

class Indicator:
    def __init__(self):
        print("indicator created")

    def rsi(self, list):
        return talib.RSI(numpy.array(list), timeperiod = 14)
