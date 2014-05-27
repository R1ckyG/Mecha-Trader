#!/usr/bin/env python
from __future__ import division
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import rsi
from pyalgotrade.broker import FixedCommission
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np, logging
from analysis import metric

logging.root.setLevel(logging.INFO)
LOWERLIMIT = 20
metrics = metric.Metrics()

class Commission(object):
  def __init__(self):
    self.value = 9
  
  def calculate(self):
    return self.value

class TrendingStrategy(strategy.Strategy):
  def __init__(self, feed, smaPeriod, tickers, trend_indicator):
    global LOWERLIMIT
    strategy.Strategy.__init__(self, feed, 2000)
    self.tickers = tickers
    self.period = smaPeriod
    self.trend_indi = trend_indicator  
    self.trend_data  = {}
    self.positions = []
    self.p_tickers = set()
    #self.getBroker().setCommission(FixedCommission(9))
    self.failed =  {}
    no_data = set()
    self.last_price = {}
    if LOWERLIMIT >= len(tickers):
      LOWERLIMIT = int(len(tickers) * .5)
    max_date = min_date = None
    import datetime
    now = datetime.datetime.now()
    start = now - datetime.timedelta(days=90)
    

    for ticker in tickers:
      data = du.get_data(ticker)
      if len(data) <= 0:
        no_data.add(ticker)
        continue
      feed.addBarsFromCSV(ticker, mongofeed.MongoRowParser())
      if max_date == None:
        max_date = data[-1]['date']
      elif max_date < data[-1]['date']:
        max_date = data[-1]['date']

      if min_date == None:
        min_date = data[0]['date']
      elif min_date > data[0]['date']:
        min_date = data[0]['date']      
      self.trend_data[ticker] = rsi.RSI(feed.getDataSeries(ticker).getAdjCloseDataSeries(), smaPeriod)
    print 'start: %r end: %r' %(min_date, max_date)
    print 'No Data: %r' % no_data
    metrics.start_date = min_date
    metrics.end_date = max_date
    metrics.num_transactions = 0
    self.start_month = min_date
  
  def onStart(self):
    print 'Initial portfolio value: %.2f' % self.getBroker().getCash()
    metrics.init_balance = self.getBroker().getCash()
  
  def onEnterCanceled(self, position):
    self.__position = None
  
  def onExitOk(self, position):
    execInfo = position.getExitOrder().getExecutionInfo()
    net_profit = position.getResult()
    inst = position.getInstrument()
    date = execInfo.getDateTime()
    metrics.num_transactions = metrics.num_transactions + 1
    if net_profit > 0:
      metrics.log_pos_returns(inst, date, net_profit)
    else:
      metrics.log_neg_returns(inst, date, net_profit)
    self.p_tickers.remove(position.getInstrument())
    print "%s: SELL %d of %s at $%.2f profit: %f" %\
                  (execInfo.getDateTime(), position.getQuantity(),
                  position.getInstrument(), execInfo.getPrice(), 
                  position.getQuantity() * position.getNetProfit())     
  
  def onExitCanceled(self, position):
    # If the exit was canceled, re-submit it.
    self.exitPosition(self.__position)
  
  def onFinish(self, bars):
    self.result = self.getBroker().getValue(bars) 
    metrics.final_balance = self.result
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
    exited = []
    excess_list = []
    
    #remove bad stock
    for pair in self.positions:
      if self.trend_data[pair[0]] and self.trend_data[pair[0]].getValue() > 80:
        exited.append(pair[1])
        excess_list.append(pair)
    for p in excess_list:
      self.positions.remove(p)
    self.exitSelected(exited)
    
    #find replacements if room in positions
    if LOWERLIMIT - len(self.positions) > 0:
      for ticker in self.tickers:
        if ticker not in self.trend_data or not self.trend_data[ticker]:continue
        rsi = self.trend_data[ticker].getValue()
        if rsi is None:
          self.failed.setdefault(ticker, 0)
          self.failed[ticker] = self.failed[ticker] + 1
          continue
        if rsi <= 25 and ticker not in self.p_tickers:
          bar = bars.getBar(ticker)
          valid_options.append((ticker, rsi, bar))
    
      valid_options = sorted(valid_options, key=lambda pair: pair[1])
      index = LOWERLIMIT - len(self.positions)
        
      #Buy companies with lowest RSI
      for pair in valid_options[:index]:
        order = (1/LOWERLIMIT) * self.getBroker().getCash()
        if pair[2] == None:continue
        order = int(order / pair[2].getClose())
        if order == 0:continue
        self.p_tickers.add(pair[0])
        position = self.enterLong(pair[0], order, True)
        self.positions = self.positions + [(pair[0], position)]
      
    #calculate metrics
    metrics.extend_period()
    for pair in self.positions:
      bar = bars.getBar(pair[0])
      self.last_price.setdefault(pair[0], None)
      if bar and self.last_price[pair[0]]:
        metrics.log_day_roc(pair[0], (bar.getClose() - self.last_price[pair[0]]) 
                                / self.last_price[pair[0]])
      if bar: self.last_price[pair[0]] = bar.getClose()
      if len(self.positions) > 0 and bar:
        curr_time = bar.getDateTime()
        diff = curr_time - self.start_month
        if diff.days  >= 30:
          print 'MO MONEYZZZ'
          cash = self.getBroker().getCash()
          self.getBroker().setCash(cash + 500)
          self.start_month = curr_time
    #self.enterSelected(valid_options[:index])'

  def onEnterOk(self, position):
    execInfo = position.getEntryOrder().getExecutionInfo()
    metrics.num_transactions = metrics.num_transactions + 1
    print "%s: BUY %d of %s at $%.2f" %\
                      (execInfo.getDateTime(), position.getQuantity(),
                      position.getInstrument(), execInfo.getPrice())
  
    
def run_strategy(period,  tickers, trend='RSI', plot=True):
  plt = None
  feed = mongofeed.MongoFeed()
  trs = TrendingStrategy(feed, period, tickers, trend)
  if plot:plt = plotter.StrategyPlotter(trs, False, False)
  if plot:
    for tick in tickers:
      continue
      plt.getInstrumentSubplot(tick).addDataSeries(tick, feed.getDataSeries(tick))
  trs.run()
  
  dd = metrics.get_all_drawdown()
  winners = metrics.get_all_win()
  losers = metrics.get_all_losses()
  avg_gain = metrics.get_all_gain()
  avg_losses = metrics.get_all_avglosses()
  returns = metrics.get_portfolio_annualized_returns()
  total_transactions = metrics.num_transactions
  metrics.build_comp_report('%s-%d-trending.txt' % (trend, LOWERLIMIT))
  print 'Failures: %r' % trs.failed
  print 'drawdown: \n%r' % (dd), 'Win percentage: \n%r ' % (winners), 'Loss perc.: \n%r' % (losers)
  print 'Gains: \n%r' % (avg_gain), '\nLosses: \n%r' % (avg_losses)
  print 'Returns: %f' % (returns)
  print 'Total Transactions: %d' % metrics.num_transactions
  print 'Value: %f, Value - Commissions: %f' % (trs.result, trs.result - (metrics.num_transactions * 7))
  if plot:plt.plot()
  return trs.result

if __name__ == '__main__':
  f = open(sys.argv[3])
  tickers = [line.strip() for line in f]
  run_strategy(int(sys.argv[1]),  tickers, sys.argv[2],plot=True) 
