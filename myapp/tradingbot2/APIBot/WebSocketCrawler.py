import websocket
from pprint import pprint
from datetime import datetime
import json
import time

from ..TradingBot.GenericTradingBot import GenericTradingBot



class WebSocketCrawler(GenericTradingBot):
    def __init__(self):
        super().__init__()
        self.host = "wss://stream.binance.com:9443/ws/"
        self.WS = [
            self.host + "!ticker@arr",
            self.host + "@ticker",
            self.host + "!miniTicker@arr"
        ]
        self.running = False
        self.active_ws = None
        self.active_url = self.WS[2]
        self.callback = None

        print("hi im web socket crawler")
              
    
    def _main(self):
        
        # websocket.enableTrace(True)
        self.active_ws = websocket.WebSocketApp(self.active_url,
                            on_open = lambda ws: self.on_open(ws),
                            on_message = lambda ws, message: self.on_message(ws, message),
                            on_error = lambda ws, error: self.on_error(ws, error),
                            on_close = lambda ws: self.on_close(ws))
        self.active_ws.run_forever()

    def on_message(self, ws, message):

            
            callback = self.callback
            if not callback:
                print("WEBSOCKET ERROR: callback is not set")
                self.stop()
                return
            callback(ws, message)

            # print(self.active_url)

    def on_error(self, ws, error):
        print("ERROR", error)

    def on_close(self, ws):
        print("### closed ###")
        
    def on_open(self, ws):
            print("web socket open")
        
        
    def stop(self):
        if self.running:
            self.running = False
            self.active_ws.keep_running = False
            print("web socket closed")
        


if __name__ == "__main__":
    a = WebSocketCrawler()
    a.start()
    time.sleep(5)
    a.stop()
    print("HELLO?")
    