#!/usr/bin/env python
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import rsi
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np

class TrendingStrategy(strategy.Strategy):
  def __init__(self, feed, smaPeriod, tickers, trend_indicator):
    strategy.Strategy.__init__(self, feed, 15000)
    self.tickers = tickers
    self.period = smaPeriod
    self.trend_indi = trend_indicator  
    self.trend_data  = {} 
    for ticker in tickers:
      data = du.get_data(ticker)
      feed.addBarsFromCSV(data, ticker)
      self.trend_data[ticker] = rsi.RSI(feed.getDataSeries(ticker), smaPeriod)     
  def 


def run_strategy(period, trend, tickers):
  feed = du.ArbiFeed()
  trs = TrendingStrategy(feed, period, tickers, trend)
if __name__ == '__main__':
  run_strategy(sys.argv[1], sys.argv[2], sys.argv[3:]) 
