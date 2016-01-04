#!/usr/bin/env python
from __future__ import division
import gc, sys, operator, scipy, datetime, multiprocessing
from scipy.special import comb
import talib as tl
import rpy2.rinterface as rinterface
rinterface.set_initoptions(('rpy2', '--max-ppsize=500000'))
rinterface.initr()
from rpy2 import robjects as ro 
from rpy2.robjects import r
from rpy2.robjects.packages import importr

#import analysis.model_learning as ml
import data.stock_data_store as sd
import numpy as np
import utils.data_util as du


s = sd.StockDataStore()
global_ticker_data = dict()
counter = multiprocessing.Value("i", 0)
total = multiprocessing.Value("i", 0)
start_time = None
lock = multiprocessing.Lock()

def get_time_left(start_time, num_complete, total):
  dtime =  datetime.datetime.now() - start_time
  time_per_ticker = dtime.total_seconds() /num_complete
  diff = total - num_complete
  return datetime.timedelta(seconds=int(time_per_ticker * diff))

def get_correlation(x, y, test=True):
  corr = r.cor(x, y)
  #r('gc()')
  #gc.collect()
  return corr

def get_t_data(ticker):
  d = s.get_company_data(ticker, retry=False)
  nd = []
  for data in d:
    nd.append(data['Adj Clos'])
  nd = np.array(nd)
  nd = tl.ROC(nd, timeperiod=7)
  return ro.FloatVector(nd[7:].tolist())
    
def get_unique_pairs(tickers):
  result = set()
  for ticker in tickers:
    for inner_tick in tickers:
      pair = "%s/%s" % (ticker, inner_tick)
      rpair = "%s/%s" % (inner_tick, ticker)
      if ticker != inner_tick and not rpair in result:
        result.add(pair)
  return result

def get_valid_tickers(tickers):
  result = []
  for ticker in tickers:
    try:
      d = s.get_company_data(ticker, retry=False)
      if d.count() != 0 and d != None:
        result.append(ticker)
        global_ticker_data[ticker] = data
      else:
        continue
    except Exception as e:
      continue
  return result

def get_correlation_wrap(pair):
  global counter, lock, global_ticker_data
  global total
  global start_time
  
  tickers = pair.split('/')
  if len(tickers) != 2: return (pair, None)
  try:
    d1 = d2 = None
    if tickers[0] in global_ticker_data:
      d1 = global_ticker_data[tickers[0]]
    else:
      d1 = get_t_data(tickers[0])
      global_ticker_data[tickers[0]] = d1
      
    if tickers[1] in global_ticker_data:
      d2 = global_ticker_data[tickers[1]]
    else:
      d2 = get_t_data(tickers[1]) 
      global_ticker_data[tickers[1]] = d2
    
    d1, d2 = du.remap_data(d1, d2)
    
    corr = get_correlation(d1, d2)
    result = (pair, corr)
    
    with lock:
      counter.value += 1
      if counter.value % 100000 == 0:
        gc.collect()
        r.gc()
        gc.collect()
        print "%.2f minutes left" % (get_time_left(start_time, counter.value, total.value).total_seconds() / 60), "%d / %d" % (counter.value, total.value)
  except Exception as e:
    print e
    return ("Fucked Up", None)
  return result

if __name__ == '__main__':
  if len(sys.argv) == 2:
    f = open(sys.argv[1])
    tickers = [ticker.strip() for ticker in f]
    f.close()
    print 'Tickers: %d Num. of combinations: %d'\
       % (len(tickers), scipy.special.comb(len(tickers), 2))
    
    #Get list of unique pairs
    tickers = get_valid_tickers(tickers)
    pairs = get_unique_pairs(tickers)
    print 'Valid tickers: %d Num. of combinations: %d'\
       % (len(tickers), len(pairs))
    pairs = list(pairs)
    total.value = len(pairs)
    start_time = datetime.datetime.now()
    
    #Get Correlations   
    c = multiprocessing.cpu_count() - 1
    slice_point = int(len(pairs) / 2)
    print 'Using %d processes' % c
    pool = multiprocessing.Pool(processes=c, maxtasksperchild=1000)
    corrs = pool.map(get_correlation_wrap, pairs)
    #print 'Closing pool 1'
    #pool.close()
    #pool.join()
    
    #print ' Starting pool 2' 
    #pool = multiprocessing.Pool(processes=c, maxtasksperchild=1000)
    #corrs2 = pool.map(get_correlation_wrap, pairs[slice_point:], chunksize=400000)
    
    #corrs.extend(corrs2)
    #Clean results
    print 'Preparing %d results' % len(corrs)
    corrs = filter(lambda x: True if type(x[1][0]) == float else False, corrs)
    corrs = [(x[0], x[1][0]) for x in corrs]
    print 'sorting'
    corrs = sorted(corrs, key=operator.itemgetter(1))
    print 'writing file'
    output = open('correlations.csv', 'w', buffering=0)
    for t in corrs:
      output.write('%s, %f\n' % t)
    output.close()
    end_time = datetime.datetime.now()
    delta = end_time - start_time
    print "Total time %.2f" % (delta.total_seconds()/ 60)

