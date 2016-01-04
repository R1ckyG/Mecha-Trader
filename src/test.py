import data.feature_extractor as fe
from datetime import datetime as dt
import numpy as np
import talib as tl

RISK_FREE = 5.0

def label_func(data, snp_vector, vector, complete_datum, index, window=1):
  if len(snp_vector) <= index + window: 
    return None
  
  windowed_index = index + window
  
  roc_vector = tl.ROC(vector, timeperiod=14)
  snp_roc = tl.ROC(snp_vector, timeperiod=14)
  beta = tl.BETA(roc_vector, snp_roc, timeperiod=14)
  
  expected_return = beta[windowed_index] * (snp_roc[windowed_index] - RISK_FREE)
  excess = beta[windowed_index] * (snp_roc[windowed_index] - RISK_FREE) + RISK_FREE
  label = 'buy' if data[windowed_index]['Open'] < data[windowed_index]['Close'] else 'stay'
  #print 'stock roc: %f, SnP roc: %f, beta: %f, exp-ret.: %f' %\
  #(roc_vector[index], snp_roc[index], beta[index], RISK_FREE + beta[index] * (snp_roc[index] - RISK_FREE)))
  
  if expected_return > 0:
    bx = 1
  else:
    bx = -1
  
  complete_datum['expected_return'] = bx
  complete_datum['excess'] = excess
  complete_datum['label'] = label 
  
  return complete_datum
 
def get_test_data():
    start = dt(2014,1,1,0,0,0,0)
    end = dt(2016,1,1,0,0,0,0)
    feature_data = fe.extract_data_from_multiple_tickers(['AAPL', 'GOOG', 'FB', 'GE', 'AMZN', 'NFLX'], start, end, label_func, 1)
    
    count = 0
    for i in feature_data:
        if i['label'] == 'buy':
            count = count + 1

    print "Distribution 0: %d, 1: %d" % (len(feature_data) - count, count)
    return feature_data

if __name__ == "__main__":
    get_test_data()