#!/usr/bin/env python
from __future__ import division
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import rsi
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np, logging

logging.root.setLevel(logging.INFO)
LOWERLIMIT = 10

class TrendingStrategy(strategy.Strategy):
  def __init__(self, feed, smaPeriod, tickers, trend_indicator):
    global LOWERLIMIT
    strategy.Strategy.__init__(self, feed, 15000)
    self.tickers = tickers
    self.period = smaPeriod
    self.trend_indi = trend_indicator  
    self.trend_data  = {}
    self.positions = []
    if LOWERLIMIT >= len(tickers):
      LOWERLIMIT = int(len(tickers) * .5)
    for ticker in tickers:
      data = du.get_data(ticker)
      feed.addBarsFromCSV(ticker, mongofeed.MongoRowParser())
      self.trend_data[ticker] = rsi.RSI(feed.getDataSeries(ticker).getAdjCloseDataSeries(), smaPeriod)
  
  def onStart(self):
    print 'Initial portfolio value: %.2f' % self.getBroker().getCash()
  
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
      self.positions.remove(position)
  
  def exitSelected(self, exit):
    for position in exit:
      self.exitPosition(position)

  def enterSelected(self, enter):
    for pair in enter:
      order = (1/LOWERLIMIT) * self.getBroker().getCash()
      order = int(order / pair[2].getClose())
      position = self.enterLong(pair[0], order, True)
      self.positions = [position] + self.positions
  
  def onBars(self, bars):
    """
    Strategy looks through all tickers and selects N with the lowest RSI values to buy.
    If the number of positions == N LIFO policy used to update.
    """
    valid_options = []
    excess = 0
    for ticker in self.tickers:
      if not self.trend_data[ticker]:continue
      rsi = self.trend_data[ticker].getValue()
      if rsi <= LOWERLIMIT:
        bar = bars.getBar(ticker)
        valid_options.append((ticker, rsi, bar))
    
    valid_options = sorted(valid_options, key=lambda pair: pair[1])
    
    if len(valid_options) >= LOWERLIMIT:
      index = LOWERLIMIT
      self.exitAll()
    elif len(valid_options) > 0:
      index = min(LOWERLIMIT, len(valid_options))
      excess = len(self.positions) + len(valid_options[:index]) - LOWERLIMIT
    else:
      return
    
    exited = []
    excess_list = []
    for i in range(excess):
      position = self.positions[i]
      excess_list.append(position)
      exited.append(position)
    
    for p in excess_list:
      self.positions.remove(p)
    
    self.exitSelected(exited)
    for pair in valid_options[:index]:
      order = (1/LOWERLIMIT) * self.getBroker().getCash()
      if pair[2] == None:continue
      order = int(order / pair[2].getClose())
      if order == 0:continue
      position = self.enterLong(pair[0], order, True)
      self.positions = [position] + self.positions
    #self.enterSelected(valid_options[:index])'

  def onEnterOk(self, position):
    execInfo = position.getEntryOrder().getExecutionInfo()
    print "%s: BUY %d of %s at $%.2f" %\
                      (execInfo.getDateTime(), position.getQuantity(),
                      position.getInstrument(), execInfo.getPrice())

    
def run_strategy(period,  tickers, trend='RSI', plot=True):
  plt = None
  feed = mongofeed.MongoFeed()
  trs = TrendingStrategy(feed, period, tickers, trend)
  if plot:plt = plotter.StrategyPlotter(trs)
  if plot:
    for tick in tickers:
      plt.getInstrumentSubplot(tick).addDataSeries(tick, feed.getDataSeries(tick))
  trs.run()
  if plot:plt.plot()
  return trs.result

if __name__ == '__main__':
  f = open(sys.argv[3])
  tickers = [line.strip() for line in f]
  run_strategy(int(sys.argv[1]),  tickers, sys.argv[2],plot=False) 
