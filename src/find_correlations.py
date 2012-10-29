#!/usr/bin/env python
from rpy2 import robjects as ro 
from rpy2.robjects import r
import talib as tl
import model_learning as ml
import stock_data_store as sd
import numpy as np
import sys, operator

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
  for ticker in tickers:
    print 'Finding Correlations for %s' % ticker
    t_data = get_t_data(ticker)
    for ticker_2 in tickers:
      tdata_2 = get_t_data(ticker_2)
      if len(t_data) != len(tdata_2):
        continue  
      corr = get_correlation(t_data, tdata_2)[0]
      ident = '%s/%s' % (ticker, ticker_2)
      corrs.append((ident, corr)) 
  print corrs
  return corrs

if __name__ == '__main__':
  if len(sys.argv) > 1:
    f = open(sys.argv[1])
    tickers = [ticker.strip() for ticker in f]
    f.close()
    print 'Tickers:', len(tickers)
    corrs = get_correlations_for_tickers(tickers)
    corrs = sorted(corrs, key=operator.itemgetter(1))
    output = open('correlations.txt', 'w', buffering=0)
    for t in corrs:
      output.write('%s, %f\n' % t)
    output.close()
    