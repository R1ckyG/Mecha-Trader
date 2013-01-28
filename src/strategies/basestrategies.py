#!/usr/bin/env python

from pyalgotrade import strategy
from analysis import metric
from utils import data_util as du
metrics = metric.Metrics()
class BaseTrender(strategy.Strategy):
  def __init__(self, feed, period, tickers, balance, row_parser):
    strategy.Strategy.__init__(self, feed, balance)
    
    self.tickers = tickers
    self.period = period
    self.last_price = {}
    self.positions = []
    max_date = min_date = None
    for ticker in tickers:
      self.last_price.setdefault(ticker, None)
      data = du.get_data(ticker)
      feed.addBarsFromCSV(ticker, row_parser())
      if max_date == None:
        max_date = data[-1]['date']
      elif max_date < data[-1]['date']:
        max_date = data[-1]['date']
      
      if min_date == None:
        min_date = data[0]['date']
      elif min_date > data[0]['date']:
        min_date = data[0]['date']    
    print 'start: %r end: %r' %(min_date, max_date)
    metrics.start_date = min_date
    metrics.end_date = max_date
  
  def onStart(self):
    print 'Initial portfolio value: %.2f' % self.getBroker().getCash()
    metrics.init_balance = self.getBroker().getCash()
  
  def onFinish(self, bars):
    self.result = self.getBroker().getValue(bars) 
    metrics.final_balance = self.result
    print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)
  
  def onEnterCanceled(self, position):
    print 'Order canceled'
    self.__position = None
  
  def onExitCanceled(self, position):
    # If the exit was canceled, re-submit it.
    self.exitPosition(self.__position)
  
  def onExitOk(self, position):
    execInfo = position.getExitOrder().getExecutionInfo()
    net_profit = position.getResult()
    inst = position.getInstrument()
    date = execInfo.getDateTime()
    if net_profit > 0:
      metrics.log_pos_returns(inst, date, net_profit)
    else:
      metrics.log_neg_returns(inst, date, net_profit)
    
    print "%s: SELL %d of %s at $%.2f profit: %f" %\
                  (execInfo.getDateTime(), position.getQuantity(),
                  position.getInstrument(), execInfo.getPrice(), 
                  position.getQuantity() * position.getNetProfit())   
  
  def onEnterOk(self, position):
    execInfo = position.getEntryOrder().getExecutionInfo()
    print "%s: BUY %d of %s at $%.2f" %\
                      (execInfo.getDateTime(), position.getQuantity(),
                      position.getInstrument(), execInfo.getPrice()) 

