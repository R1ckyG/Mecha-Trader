#!/usr/bin/env python
from __future__ import division
import operator

DEBUG = False

class Metrics:
  def __init__(self):
    self.neg_returns = {}
    self.pos_returns = {}
    self.periods = 0;
    self.day_neg_roc = {}
    self.day_pos_roc = {}
    self.tset = set()
    self.daily_roc = {} 
  
  @property
  def init_balance(self):
    return self.init_balance
  
  @init_balance.setter
  def init_balance(self, value):
    self.init_balance = value
  
  @property
  def final_balance(self):
    return self.final_balance
  
  @final_balance.setter
  def final_balance(self, value):
    self.final_balance = value

  @property
  def start_date(self):
    return self.start_date
  
  @start_date.setter
  def start_date(self, value):
    self.start_date = value
  
  @property
  def end_date(self):
    return self.end_date
  
  @end_date.setter
  def end_date(self, value):
    self.end_date = value
    
  @property
  def num_transactions(self):
    return self.num_transactions

  @num_transactions.setter
  def num_transactions(self, value):
    self.num_transactions = value

  def log_pos_returns(self, ticker, date, profit):
    self.tset.add(ticker)
    self.pos_returns.setdefault(ticker, [])
    self.pos_returns[ticker].append((date, profit))
  
  def log_neg_returns(self, ticker, date, profit):
    self.neg_returns.setdefault(ticker, [])
    self.tset.add(ticker)
    self.neg_returns[ticker].append((date, profit))
  
  def extend_period(self):
    self.periods = self.periods + 1
    
  def log_day_roc(self, ticker, roc):
    self.day_neg_roc.setdefault(ticker, [])
    self.day_pos_roc.setdefault(ticker, [])
    self.daily_roc.setdefault(ticker, [])
    self.daily_roc[ticker].append(roc)

    if roc > 0:
      self.day_pos_roc[ticker].append(roc)
    else:
      self.day_neg_roc[ticker].append(roc)
  
  def get_mae(self, ticker):
    time = len(self.pos_returns) + len(self.neg_returns)
    wins = losses = 0
    for pos in self.pos_returns[ticker]:
      wins = wins + pos[1]
    
    for pos in self.neg_returns[ticker]:
      losses = losses + pos[1]
    return  (1 / time) * (wins - losses)
  
  def find_mae(self):
    output = {}
    for ticker in self.tset:
      output[ticker] = self.get_mae(ticker)
    return output
  #TODO 
  def get_rmae(self, ticker):
    time = len(self.pos_returns) + len(self.neg_returns)
    wins = losses = 0
    for pos in self.pos_returns[ticker]:
      wins = wins + pos[1]
    
    for pos in self.neg_returns[ticker]:
      losses = losses + pos[1]
    return  (1 / time) * (wins - losses)
  #TODO
  def find_rmae(self):
    output = {}
    for ticker in self.tset:
      output[ticker] = self.get_mae(ticker)
    return output
  
  #FIX
  def get_mape(self, ticker):
    time = len(self.pos_returns) + len(self.neg_returns)
    wins = losses = 0
    for pos in self.pos_returns[ticker]:
      wins = wins + pos[1]
    
    for pos in self.neg_returns[ticker]:
      losses = losses + pos[1]
    return  (100 / time) * (wins - losses)
  
  #FIX
  def find_mape(self):
    output = {}
    for ticker in self.tset:
      output[ticker] = self.get_mape(ticker)
    return output
  
  def get_cdc(self, ticker):
    """Find correct directional change for ticker"""
    time = len(self.pos_returns) + len(self.neg_returns)
    return (100/time) * len(self.pos_returns)
  
  def get_max_dp(self, ticker):
    """Function returning max daily profit"""
    biggest = 0
    for d in self.day_pos_roc[ticker]:
      biggest = max(biggest, d)
    return biggest

  def get_all_max_dp(self):
    output = {}
    for t in self.tset:
      output[t] = self.get_max_dp(t)
    return output

  def get_all_min_dp(self):
    output = {}
    for t in self.tset:
      output[t] = self.get_min_dp(t)
    return output

  def get_min_dp(self, ticker):
    """Function returning max daily profit"""
    smallest = 0
    for d in self.day_pos_roc[ticker]:
      smallest = max(smallest, d)
    return smallest

  def get_max_drawdown(self, ticker):
    memoi = []
    self.daily_roc.setdefault(ticker, [])
    for d in range(len(self.daily_roc[ticker])):
      if d == 0:
        memoi.append((self.daily_roc[ticker][d], [self.daily_roc[ticker][d]]))
      elif memoi[d -1][0] + self.daily_roc[ticker][d] > self.daily_roc[ticker][d]:
        memoi.append((self.daily_roc[ticker][d], [self.daily_roc[ticker][d]])) 
      else:
        memoi.append((memoi[d-1][0] - self.daily_roc[ticker][d], memoi[d - 1][1]))
        memoi[d][1].append(self.daily_roc[ticker][d])
  
    maxdrawdown = 0
    sequence = None
    for d in memoi:
      if d[0] < maxdrawdown:
        maxdrawdown = d[0]
        sequence = d[1]
    if DEBUG: print 'Sequence %s \n%r %f' % (ticker, sequence, maxdrawdown)
    return maxdrawdown

  def get_all_drawdown(self):
    output = {}
    for t in self.tset:
      output[t] = self.get_max_drawdown(t)
    return output

  def get_num_winning_trade(self, ticker, normalize=False):
    if ticker not in self.pos_returns or ticker not in self.neg_returns: return 0
    wins = len(self.pos_returns[ticker])
    num_of_trades = wins + len(self.neg_returns[ticker])
    if normalize:
      end = int(wins * .95)
      l = sorted(self.pos_returns[ticker], key=operator.itemgetter(1))
      wins = len(l[:end])
      num_of_trades = end + len(self.neg_returns[ticker])
    return 100 * (wins/num_of_trades)
 
  def get_all_win(self):
    output = {}
    for t in self.tset:
      output[t] = self.get_num_winning_trade(t)
    return output

  def get_num_losing_trade(self, ticker, normalize=False):
    if ticker not in self.pos_returns or ticker not in self.neg_returns: return 0
    wins = len(self.neg_returns[ticker])
    num_of_trades = wins + len(self.pos_returns[ticker])
    
    if normalize:
      end = int(len(self.pos_returns[ticker]) * .95)
      l = sorted(self.pos_returns[ticker], key=operator.itemgetter(1))
      num_of_trades = wins + len(l[:end])
    return 100 * (wins/num_of_trades)

  def get_all_losses(self):
    output = {}
    for t in self.tset:
      output[t] = self.get_num_losing_trade(t)
    return output

  #FIX  
  def get_num_of_ups(self, ticker):
    return len(self.pos_returns[ticker])

  #FIX
  def get_num_of_downs(self, ticker):
    return len(self.neg_returns[ticker])

  def get_num_transactions(self, ticker):
    return 2 * (len(self.neg_returns[ticker]) + len(self.pos_returns[ticker]))
  
  def get_total_transactions(self):
    total = 0
    for ticker in self.neg_returns:
      total = total + 2 * len(self.neg_returns[ticker])
    for ticker in self.pos_returns:
      total = total + 2 * len(self.pos_returns[ticker])
    return total
  
  def get_total_days(self, ticker):
    return len(self.daily_roc[ticker])

  def avg_gain(self, ticker, normalize=False):
    total = 0
    v = 0
    if ticker not in self.pos_returns: return 0
    if normalize:
      l = sorted(self.pos_returns[ticker], key=operator.itemgetter(1))
      end = max(int(len(l) - (len(l) * .05)), 1)
      l = l[:end]
      for pos in l:
        total = total + pos[1]
      v = total / len(l)
    else:
      for pos in self.pos_returns[ticker]:
        total = total + pos[1]
      v = total / len(self.pos_returns[ticker])
    return v

  def get_all_gain(self):
    output = {}
    for ticker in self.tset:
      output[ticker] = self.avg_gain(ticker)
    return output
  
  def avg_losses(self, ticker, normalize=False):
    total = 0
    v = 0 
    if ticker not in self.neg_returns: return 0
    if normalize:
      l = sorted(self.neg_returns[ticker], key=operator.itemgetter(1))
      l = l[:len(l) - (len(l) * .05)]
      for pos in l:
        total = total + pos[1]
      v = total / len(l)
    else:
      for pos in self.neg_returns[ticker]:
        total = total + pos[1]
      v = total / len(self.neg_returns[ticker])
    return v

  def get_all_avglosses(self):
    output = {}
    for ticker in self.tset:
      output[ticker] = self.avg_losses(ticker)
    return output

  def get_gain_loss_ratio(self, ticker):
    return self.avg_gain(ticker) / self.avg_losses(ticker)

  def get_daily_rises(self, ticker):
    return len(self.day_pos_roc[ticker])

  def get_daily_losses(self, ticker):
    return len(self.day_neg_roc[ticker])
    
  def get_profit_factor(self, ticker, normalize=False):
    win_factor = self.get_num_winning_trade(ticker, normalize=normalize) * self.avg_gain(ticker, normalize=normalize)
    loss_factor = -1 * self.get_num_losing_trade(ticker, normalize=normalize) * self.avg_losses(ticker)
    v = 0
    try:
    	v = win_factor / loss_factor
    except:
    	print 'Uh oh: %s' % (ticker)
    return v
  
  def get_expected_gain(self, ticker, normalize=False):
    win_factor = self.get_num_winning_trade(ticker, normalize=normalize) * self.avg_gain(ticker, normalize=normalize)
    loss_factor = self.get_num_losing_trade(ticker, normalize=normalize) * self.avg_losses(ticker)
    return win_factor - loss_factor
  
  def get_portfolio_annualized_returns(self):
    gain = self.final_balance / self.init_balance
    tdiff = self.end_date - self.start_date
    years = tdiff.days / 365
    months = years * 12
    print (gain ** (12/months)), months
    gain = (gain ** (12/months)) - 1
    return gain * 100

  def build_comp_report(self, file):
    """build report for a company"""
    report_str = 'Tickers:\t'
    for ticker in self.tset:
      report_str = report_str + ticker + '\t'
    report_str = report_str + '\nWinning Trades(%):\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_num_winning_trade(ticker)) + '\t'
    
    report_str = report_str + '\nLosing Trades(%):\t' 
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_num_losing_trade(ticker)) + '\t'
    
    report_str = report_str + '\nAvg. Gain:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.avg_gain(ticker)) + '\t'
    
    report_str = report_str + '\nAvg. Loss:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.avg_losses(ticker)) + '\t'
    
    report_str = report_str + '\nProfit Factor:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_profit_factor(ticker)) + '\t'
    
    report_str = report_str + '\nExpected Gain:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_expected_gain(ticker)) + '\t'
    
    report_str = report_str + '\nNormalized Profit Factor:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_profit_factor(ticker, normalize=True)) + '\t'
    
    report_str = report_str + '\nNormalized Expected Gain:\t'
    for ticker in self.tset:
      report_str = report_str + '%.3f' % (self.get_expected_gain(ticker, normalize=True)) + '\t'
    
    f = open(file, 'w')
    f.write(report_str)
    f.close()
  
