import threading
import time
import math
import datetime

from ..OrderManager.OrderManager import OrderManager as om

class GenericTradingBot():
    def __init__(self):
        ## thread config
        super().__init__()
        self.thread_count = 0
        self.thread = None
        self.running = False
        self.exc = None
        self.buffered = 3

        print("generic bot created")
        ##

    
    def start(self):
        self.thread = threading.Thread(target = self._main, args=())
        self.thread.start()
        self.thread_count += 1
        self.running = True
        self.scheduler = None

    def _scheduler(self, callback, interval):
        
        remaining_time =  2
        scheduler = threading.Timer(interval= remaining_time, function = self._scheduler_handler, args=(callback, interval))
        scheduler.start()

        return scheduler
    
    def _scheduler_handler(self, callback, interval):

        try:
            print("now execution: ", math.floor(time.time()), " now: ", datetime.datetime.now())
            callback()
        except Exception as e:
            raise e
        

        dt = datetime.datetime.now()
        dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15)
        future_time = math.floor(dt.timestamp()) + interval + self.buffered
        remaining_time = future_time - time.time()
        print("next interval: {} - {}".format(remaining_time, datetime.datetime.fromtimestamp(future_time)))

        scheduler = threading.Timer(interval = remaining_time, function = self._scheduler_handler, args=(callback, interval))
        
        scheduler.start()

        
    def stop(self):
        self.running = False
        if self.scheduler:
            self.scheduler.cancel()
        
    def _main(self):
        
        pass
        
        #implemented by sub class
        #should handle while self.running == True
    def _raise_exc_if_any(self):
        if self.exc:
            raise self.exc
            



if __name__ == "__main__":
    tf = GenericTradingBot()
    tf.start()
            
    
        