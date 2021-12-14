import requests
from datetime import datetime
import time
import threading
import math

class AbstractCrawler:
    def __init__(self):
        super().__init__()
        
        print("abstract crawler created")
        
    
    
    
if __name__ == "__main__":
        a = AbstractCrawler()
        print(a._get_timestamp_of_start_time(360))
        print(datetime.fromtimestamp(a._get_timestamp_of_start_time(360)/1000))