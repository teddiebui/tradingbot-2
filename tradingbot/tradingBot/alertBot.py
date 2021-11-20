import playsound
import os
import time
import threading

class AlertBot:

    def __init__(self):
        self.thread = None
        self.fomoThread = None
        pass
    def _run(self):
        try:
            path = os.path.dirname(__file__) + "\\alert.m4a"
            playsound.playsound(path)
            self.thread = None
        except Exception as e:
            print(e)
    def _fomo(self):
        try:
            path = os.path.dirname(__file__) + "\\fomo.m4a"
            playsound.playsound(path)
            self.fomoThread = None
        except Exception as e:
            print(e)
    
    def alert(self):
        if self.thread == None:
            self.thread = threading.Thread(target=self._run, args=())
            self.thread.start()
    
    def fomo(self):
        if self.fomoThread == None:
            self.fomoThread = threading.Thread(target=self._fomo, args=())
            self.fomoThread.start()

if __name__ == "__main__":

    # back testing
    
    a = AlertBot()
    a.run()
