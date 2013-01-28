#!/usr/bin/env python
from __future__ import division
import operator, sys, numpy as np
from data import mongofeed
import basestrategies
from utils import data_util as du
from pyalgotrade import dataseries, plotter
from pyalgotrade.technical import cross


class BBANDStrategy(basestrategies.BaseTrender):
  def __init__(self, feed, tickers, period=9, balance=15000, limit=10):
    basestrategies.BaseTrender.__init__(self, feed, period, 
                                        tickers, balance, 
                                        mongofeed.MongoRowParser)
    self.cross_aboves = {}
    self.cross_belows = {}
    self.current_positions = set()
    self.pos_limit = limit
    params = {'timeperiod':period, 
              'nbdevup':2, 
              'nbdevdn':2, 
              'matype':du.tl.MA_SMA} 

    for ticker in self.tickers:
      print 'Initializing: %s' % (ticker)
      data = du.get_data(ticker)
      d = [v['Adj Clos'] for v in data]
      a, b, c = du.run_command( 
                          'BBANDS',
                          np.array(d),
                          **params
                        )
      
      highs = dataseries.SequenceDataSeries([d for d in a.tolist()]) 
      lows = dataseries.SequenceDataSeries([d for d in c.tolist()]) 
      mids = dataseries.SequenceDataSeries([d for d in b.tolist()])
      
      self.cross_aboves[ticker] = cross.CrossAbove(feed.getDataSeries(ticker)
                                            .getAdjCloseDataSeries(), highs)  
      self.cross_belows[ticker] = cross.CrossBelow(feed.getDataSeries(ticker)
                                            .getAdjCloseDataSeries(), lows)
  
  def onBars(self, bars):
    valid_options = []
    cross_values = 0
    for ticker in self.tickers:
      if ticker in self.current_positions \
        or self.cross_belows[ticker] is None: continue
      cross_values = self.cross_belows[ticker].getValue()
      if cross_values > 0:
        valid_options.append((ticker, cross_values, bars.getBar(ticker)))
    if len(valid_options) == 0: return
    basestrategies.metrics.extend_period()
    valid_options = sorted(valid_options, key=operator.itemgetter(1))
    if len(valid_options) > self.pos_limit:
      valid_options = valid_options[:self.pos_limit]
    sell = []
    for i in range(len(valid_options)):
      if len(valid_options) + len(self.positions) > self.pos_limit:
        pos = self.positions.pop(0)
        if pos[0] in self.current_positions:
        	self.current_positions.remove(pos[0])
        else:
        	print self.current_positions, pos[0]
        sell.append(pos[1])
    for position in sell:
      self.exitPosition(position)
    for option in valid_options:
      self.current_positions.add(option[0])
      order = (1 / self.pos_limit) * (self.getBroker().getCash() / option[2].getClose())
      position = self.enterLong(option[0], order, True)
      self.positions.append((option[0], position))

def run_strategy(period, tickers, balance=15000, limit=10, plot=True):
  plt = None
  feed = mongofeed.MongoFeed()
  trs = BBANDStrategy(feed, tickers, period, balance, limit)
  if plot:plt = plotter.StrategyPlotter(trs, False, False)
  if plot:
    for tick in tickers:
      continue
      plt.getInstrumentSubplot(tick).addDataSeries(tick, feed.getDataSeries(tick))
  trs.run()
  
  #dd = basestrategies.metrics.get_all_drawdown()
  winners = basestrategies.metrics.get_all_win()
  losers = basestrategies.metrics.get_all_losses()
  avg_gain = basestrategies.metrics.get_all_gain()
  avg_losses = basestrategies.metrics.get_all_avglosses()
  returns = basestrategies.metrics.get_portfolio_annualized_returns()
  basestrategies.metrics.build_comp_report('bband-trending.txt')
  print 'Win percentage: \n%r\n' % (winners), 'Loss perc.: \n%r' % (losers)
  print 'Gains: \n%r\n' % (avg_gain), 'Losses: \n%r' % (avg_losses)
  print 'Returns: %f' % (returns)
  if plot:plt.plot()
  return trs.result
  
if __name__ == '__main__':
  f = open(sys.argv[1], 'r')
  tickers = [t.strip() for t in f]
  run_strategy(int(sys.argv[2]), tickers, plot=False)

