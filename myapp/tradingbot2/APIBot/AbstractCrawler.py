import requests
from datetime import datetime
import time
import threading
import math

class AbstractCrawler:
    def __init__(self):
        super().__init__()
        self.host = "https://api.binance.com"
        self.req = requests.Session()
        self.timer = None
        print("abstract crawler created")
        
    
    def _timestamp(self, start_day):
        dt = datetime.now()
        t = (math.floor(time.time()) - start_day * 24 * 60 * 60)
        if start_day == 0:
            t = t - 15*60
        return t * 1000
        # dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15, day = dt.day - start_day)
        # return str(int(dt.timestamp()*1000))
    
    def klines_url(self, symbol, startTime, endTime, inverval, limit):
        url = self.host + "/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}&endTime={}".format(symbol, "15m", limit, startTime * 1000, endTime * 1000)
        # print(url)
        return url
    
if __name__ == "__main__":
        a = AbstractCrawler()
        print(a._get_timestamp_of_start_time(360))
        print(datetime.fromtimestamp(a._get_timestamp_of_start_time(360)/1000))