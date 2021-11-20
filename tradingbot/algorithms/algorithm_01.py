from datetime import datetime as dt
def run(candles, indicator):

	indicator.refresh_rsi([i['close'] for i in candles])

	if indicator.rsi[-1] < 30:
		# print(dt.fromtimestamp(float(candles[-1]['time'])/1000), indicator.rsi[-1])
		return True

