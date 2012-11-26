#!/usr/bin/env python
from __future__ import division
import gc, sys, operator, scipy, datetime, multiprocessing
from rpy2 import robjects as ro 
from rpy2.robjects import r
from rpy2.robjects.packages import importr
import lib.talib as tl
import analysis.model_learning as ml
import data.stock_data_store as sd
import numpy as np
import utils.data_util as du
def get_time_left(start_time, num_complete, total):
  dtime =  datetime.datetime.now() - start_time
  time_per_ticker = num_complete / dtime.total_seconds()
  diff = total - num_complete
  return datetime.timedelta(seconds=int(time_per_ticker * diff))

s = sd.StockDataStore()
def get_correlation(x, y, test=True):
  corr = r.cor(x, y)
  return corr

def get_t_data(ticker):
  d = s.get_company_data(ticker)
  nd = []
  for data in d:
    nd.append(data['Adj Clos'])
  nd = np.array(nd)
  nd = tl.ROC(nd, timeperiod=7)
  return ro.FloatVector(nd[7:].tolist())
    
def get_correlations_for_tickers(tickers):
  corrs = []
  start_time = datetime.datetime.now()
  first = True
  for ticker in tickers:
    if  not first:
      time_left =  get_time_left(
                       start_time, 
                       len(corrs), 
                       scipy.misc.comb(len(tickers), 2)
                     )
      print 'Finding Correlations for %s. Time remaining: %f minutes' % (ticker,time_left.seconds/60)
    first = False
    t_data = get_t_data(ticker)
    for ticker_2 in tickers:
      tdata_2 = get_t_data(ticker_2)
      if len(t_data) != len(tdata_2):
        t_data, tdata_2 = du.remap_data(t_data, tdata_2)  
      corr = get_correlation(t_data, tdata_2)[0]
      ident = '%s/%s' % (ticker, ticker_2)
      corrs.append((ident, corr)) 
      r('gc()')
      gc.collect()
    gc.collect()
  return corrs

def compute_spread(s_1, s_2, beta):
  if len(s_1) != len(s_2):
    return
  spread = []
  for i in range(len(s_1)):
    diff = s_1[i] - s_2[i] * beta
    spread.append(diff) 
  return spread
  
def garbage_collect(garbage):
  for trash in garbage:
    r('rm(%s)' % trash)
  r('gc(FALSE)')


def get_adf(t1, t2, spread=False, portion=0):
  d1 = s.get_company_data(t1)
  d2 = s.get_company_data(t2)
  
  l1 = []
  for d in d1:
    l1.append(d['Adj Clos'])
  l2 = []
  for d in d2:
    l2.append(d['Adj Clos'])
  if len(l1) != len(l2):
    l1, l2 = du.remap_data(l1, l2)
  l1 = l1[int(len(l1) * portion):]
  l2 = l2[int(len(l2) * portion):]  
  r.assign('l1', ro.FloatVector(l1))
  r.assign('l2', ro.FloatVector(l2))
  t1 = t1.replace('^', '')
  t2 = t2.replace('^', '')
  try:
    df = r('data.frame(%s=l1, %s=l2)' % (t1, t2))
  except:
    command = 'data.frame(%s=l1, %s=l2)' % (t1, t2)
    print 'ErRROR: %s' %  command
    return None
  r.assign('df', df)
  command = 'm <- lm(%s ~ %s + 0, data=df)' % (t1, t2)
  r(command)
  beta = r('coef(m)[1]')[0]
  sprd = compute_spread(l1, l2, beta)
  r.assign('sprd', ro.FloatVector(sprd))
  importr('tseries')
  r('ht <- adf.test(sprd, alternative="stationary", k=0)')
  #r('cat("ADF p-value is", ht$p.value, "\n")')
  p = r('ht$p.value')
  garbage_collect(['ht', 'sprd', 'l1', 'm', 'l2', 'df'])
  gc.collect()
  if spread:
    return p[0],sprd, beta   
  return p[0]

def is_significant(p_value, threshold=.05):
  result = True if p_value < threshold else False
  return result

def get_all_adf(tickers):
  adf = []
  first = True
  start_time = datetime.datetime.now()
  for ticker in tickers:
    if  not first:
      time_left =  get_time_left(
                       start_time, 
                       len(adf), 
                       scipy.misc.comb(len(tickers), 2)
                     )
      print 'Finding cointegration for %s. Time remaining: %f minutes' % (ticker,time_left.seconds/60)
    first = False
    for ticker_2 in tickers:
      if ticker == ticker_2: continue
      p = get_adf(ticker, ticker_2)
      if p is None: continue
      adf.append(('%s/%s' % (ticker, ticker_2), p, is_significant(p)))
  return adf
  
def combine_tickers(tickers):
  tl = []
  for ticker in tickers:
    for ticker_2 in  tickers:
      if ticker == ticker_2: continue
      tl.append('%s/%s' % (ticker, ticker_2))
  return tl

def get_formatted_adf(t_combo):
  t1, t2 = t_combo.split('/')
  try:
    p = get_adf(t1, t2)
    result = ('%s/%s' % (t1, t2), p, is_significant(p))
  except:
    print 'F#CK#D up %s' % t_combo
    result = None
  return result 
    
if __name__ == '__main__':
  if len(sys.argv) == 2:
    f = open(sys.argv[1])
    tickers = [ticker.strip() for ticker in f]
    f.close()
    print 'Tickers: %d Num. of combinations: %d'\
       % (len(tickers), scipy.misc.comb(len(tickers), 2))
    corrs = get_correlations_for_tickers(tickers)
    corrs = sorted(corrs, key=operator.itemgetter(1))
    output = open('correlations.txt', 'w', buffering=0)
    for t in corrs:
      output.write('%s, %f\n' % t)
    output.close()
  elif len(sys.argv) > 2:
    f = open(sys.argv[1])
    tickers = [ticker.strip() for ticker in f]
    c_tickers = combine_tickers(tickers)
    c = multiprocessing.cpu_count()
    print 'Using %d processes' % c
    pool = multiprocessing.Pool(processes=c - 1)
    result = pool.imap_unordered(get_formatted_adf, c_tickers, chunksize=500)
    result = filter(lambda x: True if x[1] else False, result)
    result = sorted(result, key=operator.itemgetter(1))
    output = open('adf.txt', 'w', buffering=0)
    for t in result:
      output.write('%s, %f, %s,\n' % t)
    output.close() 
