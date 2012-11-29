#!/usr/bin/env python
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import rsi
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np

LOWERLIMIT = 10

class TrendingStrategy(strategy.Strategy):
  def __init__(self, feed, smaPeriod, tickers, trend_indicator):
    strategy.Strategy.__init__(self, feed, 15000)
    self.tickers = tickers
    self.period = smaPeriod
    self.trend_indi = trend_indicator  
    self.trend_data  = {}
    self.positions = []
    for ticker in tickers:
      data = du.get_data(ticker)
      feed.addBarsFromCSV(data, ticker)
      self.trend_data[ticker] = rsi.RSI(feed.getDataSeries(ticker), smaPeriod)
  
  def onStart(self):
  	print 'Initial portfolio value: %.2f' % self.getBroker().getCash()
  
  def onEnterOK(self, position):
  	execInfo = postion.getEntryOrder().getExecutionInfo()
		print "%s: BUY %d of %s at $%.2f" %\
						 					(execInfo.getDateTime(), position.getQuantity(),
                      position.getInstrument(), execInfo.getPrice())
  
  def onEnterCanceled(self, position):
    self.__position = None
  
  def onExitOk(self, position):
		execInfo = position.getExitOrder().getExecutionInfo()
		print "%s: SELL %d of %s at $%.2f profit: %f" %\
									(execInfo.getDateTime(), position.getQuantity(),
									position.getInstrument(), execInfo.getPrice(), 
									position.getQuantity() * position.getNetProfit())     
	
	def onExitCanceled(self, position):
		# If the exit was canceled, re-submit it.
		self.exitPosition(self.__position)
	
	def onFinish(self, bars):
		self.result = self.getBroker().getValue(bars) 
		print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)
	
	def exitAll(self):
		for position in self.positions:
			self.exitPosition(position)
	
	def onBars(self, bars):
		"""
		Strategy looks through all tickers and selects N with the lowest RSI values to buy.
		If the number of positions == N LIFO policy used to update.
		"""
		valid_options = []
		for ticker in self.tickers:
			if not self.trend_data[ticker]:continue
			rsi = self.trend_data[ticker].getValue()
			if rsi <= LOWERLIMIT:
				valid_options.append((ticker, rsi))
		
		valid_options = sorted(valid_options, key=lambda pair: pair[1])
		
		if len(valid_options) == len(self.positions) and len(self.positions) >= LOWER_LIMIT:
			self.exitAll()
		else:
			index = min(LOWER_LIMIT, len(valid_options))
			self.positions += valid_options[:index]
			excess = len(self.position) - LOWERLIMIT
		
		exited = []
		for i in range(excess):
			exited.append(self.positions.pop(i))
		self.exitSelected(
def run_strategy(period, trend, tickers):
  feed = du.ArbiFeed()
  trs = TrendingStrategy(feed, period, tickers, trend)
if __name__ == '__main__':
  run_strategy(sys.argv[1], sys.argv[2], sys.argv[3:]) 
