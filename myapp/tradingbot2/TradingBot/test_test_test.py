import json
import datetime
import time
class Test:
    def __init__(self):
        with open(r"C:\Users\teddi\Desktop\temp\tradingbot-2\myapp\tradingbot2\jsondata\klines\BTCUSDT.json", "r") as f:
            data = json.load(f)
            for i in range(len(data[:])):


                
                # if i == 0:
                #     continue
                candle = data[i]
                timestamp = int(candle[0]/1000)
                print(datetime.datetime.fromtimestamp(timestamp))
                
                # if timestamp - 15*60 != int(data[i-1][0]/1000):
                #     print("ERROR")

                #     print(datetime.datetime.fromtimestamp(timestamp), datetime.datetime.fromtimestamp(int(data[i-1][0]/1000)))
                #     time.sleep(1)
            print("len(data): ", len(data))


if __name__ == "__main__":
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    t = Test();
    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")
