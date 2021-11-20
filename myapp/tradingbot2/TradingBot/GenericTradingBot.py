import threading
import time
import math
from datetime import datetime

from ..OrderManager.OrderManager import OrderManager as om

class GenericTradingBot():
    def __init__(self):
        ## thread config
        self.thread_count = 0;
        self.thread = None
        self.running = False
        self.exc = None
        self.INTERVAL = 15 * 60
        
        ##
    
    def start(self):
        self.thread = threading.Thread(target = self._main, args=());
        self.thread.start()
        self.thread_count += 1
        
        
        self.thread.join()
        self._raise_exc_if_any()
        
    def stop(self):
        self.running = False
        
    def _call_back(self):
        pass
        #implemented by sub class

    def _next_15m_timer(self, callback):
        
        dt = datetime.now()
        dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15)
        future_time = math.floor(dt.timestamp()) + self.INTERVAL
        remaining_time = future_time - time.time() + 2

        self.timer = threading.Timer(interval= remaining_time, function = self._next_15m_timer_handler, args=(callback, self.INTERVAL))
        print("next interval: ", future_time - time.time())

        return self.timer
    
    def _next_15m_timer_handler(self, callback, interval):
        print("now execution: ", math.floor(time.time()), " now: ", datetime.now())
        future_time = math.floor(time.time()) + interval
        remaining_time = 2
        print("next interval: {} ({})".format(remaining_time, datetime.fromtimestamp(remaining_time)))
        self.timer = threading.Timer(interval = future_time - time.time(), function = self._next_15m_timer_handler, args=(callback, interval))
        self.timer.start()
        
        callback()

    
    def _raise_exc_if_any(self):
        if self.exc:
            raise self.exc
            



if __name__ == "__main__":
    tf = GenericTradingBot()
    tf.start()
            
    
        