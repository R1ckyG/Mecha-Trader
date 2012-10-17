#!/usr/bin/env python
import numpy as np
import talib as tl
import stock_data_store, sys

RISK_FREE = 5.0

def make_data_vectors(data):
  """Utility function taking a list of dicts and returning arrays"""
  result_dict = {'adjusted_close': list(), 
                 'raw_close': list(),
                 'high': list(),
                 'low': list(),
                 'open':list(),
                 'volume': list(),
                 'date': list()
                }
  for datum in data:
    result_dict['adjusted_close'].append(datum['Adj Clos']) if \
        'Adj Clos' in datum else result_dict['adjusted_close'].append(None)
    result_dict['raw_close'].append(datum['Close']) if \
        'Close' in datum else result_dict['raw_close'].append(None)
    result_dict['high'].append(datum['High']) if \
        'High' in datum else result_dict['high'].append(None)
    result_dict['low'].append(datum['Low']) if 'Low' in datum \
        else result_dict['low'].append(None)
    result_dict['open'].append(datum['Open']) if 'Open' in datum \
        else result_dict['open'].append(None)
    result_dict['volume'].append(datum['Volume']) if 'Volume' in datum \
        else result_dict['volume'].append(None)
    result_dict['date'].append(datum['date']) if 'date' in datum \
        else result_dict['date'].append(None)

  volume = np.array(result_dict['volume'])
  adj_close = np.array(result_dict['adjusted_close'])
  close = np.array(result_dict['raw_close'])
  high = np.array(result_dict['high'])
  low = np.array(result_dict['low'])
  open_p = np.array(result_dict['open'])
  date = np.array(result_dict['date'])

  return {'open':open_p, 'close':close, 'low':low, 
          'high':high, 'adj_close':adj_close, 
          'volume':volume, 'date':date}


def get_feature_from_vector(vector):
  feature_dict = {}
  
  feature_dict['ema_10'] = tl.EMA(vector, timeperiod=10)
  feature_dict['ema_16'] = tl.EMA(vector, timeperiod=16)
  feature_dict['ema_22'] = tl.EMA(vector, timeperiod=22)

  feature_dict['sma_10'] = tl.SMA(vector, timeperiod=10)
  feature_dict['sma_16'] = tl.SMA(vector, timeperiod=16)
  feature_dict['sma_22'] = tl.SMA(vector, timeperiod=22)
  
  upper, middle, lower = tl.BBANDS(vector, timeperiod=20, nbdevup=2, 
                                   nbdevdn=2, matype=tl.MA_SMA)
  feature_dict['bbands_20_upper'] = upper
  feature_dict['bbands_20_lower'] = lower

  upper, middle, lower = tl.BBANDS(vector, timeperiod=26, nbdevup=2, 
                                   nbdevdn=2, matype=tl.MA_SMA)
  feature_dict['bbands_26_upper'] = upper
  feature_dict['bbands_26_lower'] = lower

  upper, middle, lower = tl.BBANDS(vector, timeperiod=32, nbdevup=2, 
                                   nbdevdn=2, matype=tl.MA_SMA)
  feature_dict['bbands_32_upper'] = upper
  feature_dict['bbands_32_lower'] = lower
  feature_dict['momentum_12'] = tl.MOM(vector, timeperiod=12)
  feature_dict['momentum_18'] = tl.MOM(vector, timeperiod=18)
  feature_dict['momentum_24'] = tl.MOM(vector, timeperiod=24)
  
  ema = tl.EMA(feature_dict['momentum_12'], timeperiod=2)
  feature_dict['momentum_to_ema_12'] = np.divide(feature_dict['momentum_12'], ema) 
  feature_dict['ema_to_mom_12'] = ema
  ema = tl.EMA(feature_dict['momentum_18'], timeperiod=2)
  feature_dict['momentum_to_ema_18'] = np.divide(feature_dict['momentum_18'], ema) 
  feature_dict['ema_to_mom_18'] = ema
  ema = tl.EMA(feature_dict['momentum_24'], timeperiod=2)
  feature_dict['momentum_to_ema_24'] = np.divide(feature_dict['momentum_24'], ema) 
  feature_dict['ema_to_mom_24'] = ema
  return feature_dict

def apply_bollinger_rule(close_prices, features):
  rule_array = []
  for i in range(len(features['bbands_26_lower'])):
    if tl.nan == features['bbands_26_lower'][i]:
      rule_array.append('hold')
    elif close_prices[i - 1] >= features['bbands_26_lower'][i] \
      and close_prices[i] < features['bbands_26_upper'][i]:
      rule_array.append('buy')
    elif close_prices[i - 1] <= features['bbands_26_lower'][i] \
      and close_prices[i] > features['bbands_26_upper'][i]:
      rule_array.append('sell')
      print 'sell'
    else:
      rule_array.append('hold')
  return rule_array

def apply_momentum_rule(features, days=24):
  rule_array = []
  ratio_key = 'ema_to_mom_%d' % days
  momentum_key = 'momentum_%d' % days
  for i in range(len(features[ratio_key])): 
    if tl.nan == features[ratio_key][i]:
      rule_array.append('hold') 
    elif features[momentum_key][i - 1] <= features[ratio_key][i]\
      and features[momentum_key][i] > features[ratio_key][i]:
      rule_array.append('buy')
    elif features[momentum_key][i - 1] >= features[ratio_key][i]\
      and features[momentum_key][i] < features[ratio_key][i]:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
  print rule_array
  return rule_array
 
def complete_datapoint(datum, feature_set, index):
  for metric in feature_set:
    metric_features = feature_set[metric]
    if metric == 'bband_rule': 
      datum[metric] = metric_features[index]
      continue
    elif metric.startswith('momentum_rule'):
      datum[metric] = metric_features[index]
      continue
    for feature in metric_features:
      key = '%s_%s' %(metric, feature)
      datum[key] = metric_features[feature][index]
  return datum

def get_features_from_vectors(data_vectors):
  feature_dict = {}
  for vector in data_vectors:
    if vector == 'date': continue
    print 'Extracting features from %s' % vector
    features = get_feature_from_vector(data_vectors[vector])
    feature_dict[vector+'_features'] = features
  print 'Applying bollinger trading rule'
  feature_dict['bband_rule'] = apply_bollinger_rule(
                                          data_vectors['adj_close'], 
                                          feature_dict['adj_close_features']
                                        )
  feature_dict['momentum_rule_12'] = apply_momentum_rule(
                                          feature_dict['adj_close_features'],
                                          days=12
                                        )
  feature_dict['momentum_rule_18'] = apply_momentum_rule(
                                          feature_dict['adj_close_features'],
                                          days=18
                                        )
  feature_dict['momentum_rule_24'] = apply_momentum_rule(
                                          feature_dict['adj_close_features'],
                                          days=24
                                        )

  return feature_dict

snp_vector = None
def find_bxret(data, snp_vector, vector, index):
  roc_vector = tl.ROC(vector, timeperiod=14)
  snp_roc = tl.ROC(snp_vector, timeperiod=14)
  beta = tl.BETA(roc_vector, snp_roc, timeperiod=14)
  expected_return = beta[index] * (snp_roc[index] - RISK_FREE)
  excess = beta[index] * (snp_roc[index] - RISK_FREE) + RISK_FREE
  #print 'stock roc: %f, SnP roc: %f, beta: %f, exp-ret.: %f' %\
  #(roc_vector[index], snp_roc[index], beta[index], RISK_FREE + beta[index] * (snp_roc[index] - RISK_FREE))
  if expected_return > 0:
    return 1, excess
  else:
    return -1, excess
  
def combine(data, vectors, features):
  print len(data), len(vectors['close'])
  results = []
  sds = stock_data_store.StockDataStore()
  print 'timespan:', data[0]['date'], data[-1]['date']
  snp_data = sds.get_company_data(
                            '^GSPC'
                            ,start_date=data[0]['date']
                            ,end_date=data[-1]['date']
                          )
  datam = []
  for d in snp_data:
    datam.append(d)
  vectored = make_data_vectors(datam)
  snp_vector = vectored['adj_close']
  print len(data) == len(snp_vector), len(data), len(snp_vector)
  for i in range(len(data)):
    complete_datum = complete_datapoint(data[i], features, i)
    bx, excess = find_bxret(data, snp_vector, vectors['adj_close'], i)
    complete_datum['bxret'] = bx
    complete_datum['excess'] = excess
    results.append(complete_datum)
  return results

def extract_data(data_cursor):
  data = []
  for datum in data_cursor:
    data.append(datum)
  vectors = make_data_vectors(data)
  features = get_features_from_vectors(vectors)
  processed_data = combine(data, vectors, features)
  return processed_data

def get_features(ticker):
  data_store = stock_data_store.StockDataStore()
  data = data_store.get_company_data(ticker)
  processed_data = extract_data(data)
  return processed_data

if __name__=='__main__':
  if len(sys.argv) > 1:
    tickers = []
    f = open(sys.argv[1], 'r')
    data_store = stock_data_store.StockDataStore()  
    for line in f:
      tickers.append(line.strip())
    
    data_dict = {}
    for ticker in tickers:
      print 'Making data for %s' % ticker
      data = data_store.get_company_data(ticker)
      processed_data = extract_data(data)
      data_store.save_data(ticker, processed_data)      
