from datetime import datetime as dt
def run(candles, indicator):

	# return False
	condition1 = indicator.validate_rsi(candles)
	condition2 = indicator.validate_macd(candles)

	if condition1 == True and condition2 == True:
		return True

	# if indicator.validate_rsi(candles) and indicator.validate_macd(candles):
	# 	return True