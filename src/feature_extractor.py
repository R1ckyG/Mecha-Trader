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


def get_feature_from_vector(vector, dtype=None):
  feature_dict = {}
  
  feature_dict['ema_10'] = tl.EMA(vector, timeperiod=10)
  feature_dict['ema_16'] = tl.EMA(vector, timeperiod=16)
  feature_dict['ema_22'] = tl.EMA(vector, timeperiod=22)

  feature_dict['sma_10'] = tl.SMA(vector, timeperiod=10)
  feature_dict['sma_16'] = tl.SMA(vector, timeperiod=16)
  feature_dict['sma_22'] = tl.SMA(vector, timeperiod=22)
  
  if dtype == 'adj_close':
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

    feature_dict['rate_of_change_10'] = tl.ROCP(vector, timeperiod=10)
    feature_dict['rate_of_change_16'] = tl.ROCP(vector, timeperiod=16)
    feature_dict['rate_of_change_22'] = tl.ROCP(vector, timeperiod=22)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=18)[0]
    feature_dict['macd_0_18'] = macd 
    ema = tl.EMA(feature_dict['macd_0_18'], timeperiod=9)
    feature_dict['macds_0_18'] = ema
    feature_dict['macdsr_0_18'] = np.divide(feature_dict['macd_0_18'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=18)[1]
    feature_dict['macd_1_18'] = macd 
    ema = tl.EMA(macd, timeperiod=9)
    feature_dict['macds_1_18'] = ema
    feature_dict['macdsr_1_18'] = np.divide(feature_dict['macd_1_18'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=18)[2]
    feature_dict['macd_2_18'] = macd 
    ema = tl.EMA(macd, timeperiod=9)
    feature_dict['macds_2_18'] = ema
    feature_dict['macdsr_2_18'] = np.divide(feature_dict['macd_2_18'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=24)[0]
    feature_dict['macd_0_24'] = macd 
    ema = tl.EMA(feature_dict['macd_0_24'], timeperiod=9)
    feature_dict['macds_0_24'] = ema
    feature_dict['macdsr_0_24'] = np.divide(feature_dict['macd_0_24'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=24)[1]
    feature_dict['macd_1_24'] = macd 
    ema = tl.EMA(feature_dict['macd_1_24'], timeperiod=9) 
    feature_dict['macds_1_24'] = ema
    feature_dict['macdsr_1_24'] = np.divide(feature_dict['macd_1_24'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=24)[2]
    feature_dict['macd_2_24'] = macd 
    ema = tl.EMA(feature_dict['macd_2_24'], timeperiod=9) 
    feature_dict['macds_2_24'] = ema
    feature_dict['macdsr_2_24'] = np.divide(feature_dict['macd_2_24'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=30)[0]
    feature_dict['macd_0_30'] = macd  
    ema = tl.EMA(feature_dict['macd_0_30'], timeperiod=9)
    feature_dict['macds_0_30'] = ema
    feature_dict['macdsr_0_30'] = np.divide(feature_dict['macd_0_30'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=30)[1]
    feature_dict['macd_1_30'] = macd  
    ema = tl.EMA(feature_dict['macd_1_30'], timeperiod=9)
    feature_dict['macds_1_30'] = ema
    feature_dict['macdsr_1_30'] = np.divide(feature_dict['macd_1_30'], ema)

    macd = tl.MACD(vector, fastperiod=12, slowperiod=30)[2]
    feature_dict['macd_2_30'] = macd  
    ema = tl.EMA(feature_dict['macd_2_30'], timeperiod=9)
    feature_dict['macds_2_30'] = ema
    feature_dict['macdsr_2_30'] = np.divide(feature_dict['macd_2_30'], ema)

    feature_dict['rsi_8'] = tl.RSI(vector, timeperiod=8)
    feature_dict['rsi_14'] = tl.RSI(vector, timeperiod=14)
    feature_dict['rsi_20'] = tl.RSI(vector, timeperiod=20)
  return feature_dict

def get_stoch_features(close, high, low, days=12):
  slowk, slowd = tl.STOCH(high, low, close, fastk_period=days, 
                          slowk_period=3, slowk_matype=tl.MA_SMA,
                          slowd_period=3, slowd_matype=tl.MA_SMA)
  fastk, fastd = tl.STOCHF(high, low, close, fastk_period=days,
                          fastd_period=3, fastd_matype=tl.MA_SMA)
  results = dict()
  results['slowk_%d' % days] = slowk
  results['slowd_%d' % days] = slowd
  results['fastk_%d' % days] = fastk
  results['fastd_%d' % days] = fastd
  return results

def apply_rsi_rule(features, days=8):
  rule_array = []
  key = 'rsi_%d' % days
  for i in range(len(features[key])):
    if tl.nan == features[key][i]:
      rule_array.append('hold')
    elif features[key][i - 1] >= 30\
      and features[key][i] < 70:
      rule_array.append('buy')
    elif features[key][i -1] <= 30\
      and features[key][i] > 70:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
  return rule_array

def apply_stoch_fast_rule(features, days=12):
  rule_array = []
  dkey = 'fastd_%d' % days
  kkey = 'fastk_%d' % days
  for i in range(len(features[dkey])):
    if tl.nan == features[kkey][i]:
      rule_array.append('hold')
    elif features[kkey][i -1] <= features[dkey][i]\
      and features[kkey][i] > features[dkey][i]:
      rule_array.append('buy')
    elif features[kkey][i -1] >= features[dkey][i]\
      and features[kkey][i] < features[dkey][i]:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
  return rule_array

def apply_stoch_slow_rule(features, days=12):
  rule_array = []
  dkey = 'slowd_%d' % days
  kkey = 'slowk_%d' % days
  for i in range(len(features[dkey])):
    if tl.nan == features[kkey][i]:
      rule_array.append('hold')
    elif features[kkey][i -1] <= features[dkey][i]\
     and features[kkey][i] > features[dkey][i]:
      rule_array.append('buy')
    elif features[kkey][i -1] >= features[dkey][i]\
     and features[kkey][i] < features[dkey][i]:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
  return rule_array

def apply_macd_rule(features, index=0, days=18):
  rule_array = []
  key = 'macd_%d_%d' % (index, days)
  macds_key = 'macds_%d_%d' % (index, days)
  for i in range(len(features[key])):
    if tl.nan == features[key][i]:
      rule_array.append('hold')
    elif features[key][i - 1] <= features[macds_key][i]\
      and features[key][i] > features[macds_key][i]:
      rule_array.append('buy')
    elif features[key][i - 1] >= features[macds_key][i]\
      and features[key][i] < features[macds_key][i]:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
  return rule_array

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
  return rule_array
 
def apply_roc_rule(features, days=12):
  key = 'rate_of_change_%d' % days
  rule_array = []
  for i in range(len(features[key])):
    if tl.nan == features[key][i]:
      rule_array.append('hold')
    elif features[key][i] > 0 and features[key][i-1] <= 0:
      rule_array.append('buy')
    elif features[key][i] < 0 and features[key][i-1] >= 0:
      rule_array.append('sell')
    else:
      rule_array.append('hold')
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
    elif metric.startswith('roc_rule'):
      datum[metric] = metric_features[index]
      continue
    elif metric.startswith('macd_rule'):
      datum[metric] = metric_features[index]
      continue
    elif metric.startswith('rsi_rule'):
      datum[metric] = metric_features[index]
      continue
    elif metric.startswith('fast'):
      datum[metric] = metric_features[index]
      continue
    elif metric.startswith('slow'):
      datum[metric] = metric_features[index]
      continue
    for feature in metric_features:
      key = '%s_%s' %(metric, feature)
      try:
        datum[key] = metric_features[feature][index]
      except:
        print 'Uh oh', key
        pass 
  return datum

def get_features_from_vectors(data_vectors):
  feature_dict = {}
  for vector in data_vectors:
    if vector == 'date': continue
    print 'Extracting features from %s' % vector
    features = get_feature_from_vector(data_vectors[vector], dtype=vector)
    feature_dict[vector+'_features'] = features
  
  close = data_vectors['adj_close']
  high = data_vectors['high']
  low = data_vectors['low']
  feature_dict.update(get_stoch_features(close, high, low, days=12))
  feature_dict.update(get_stoch_features(close, high, low, days=18))
  feature_dict.update(get_stoch_features(close, high, low, days=24))
  
  print 'Applying bollinger rule'
  feature_dict['bband_rule'] = apply_bollinger_rule(
                                          data_vectors['adj_close'], 
                                          feature_dict['adj_close_features']
                                        )
  print 'Applying momentum rules'
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
  print 'Applying rate of change rules'
  feature_dict['roc_rule_10'] = apply_roc_rule(
                                          feature_dict['adj_close_features'],
                                          days=10
                                        )
  feature_dict['roc_rule_16'] = apply_roc_rule(
                                          feature_dict['adj_close_features'],
                                          days=16
                                        )
  feature_dict['roc_rule_22'] = apply_roc_rule(
                                          feature_dict['adj_close_features'],
                                          days=22
                                        )
  print 'Applying MACD rules'
  feature_dict['macd_rule_0_18'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=0,
                                          days=18
                                        )
  feature_dict['macd_rule_0_24'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=0,
                                          days=24
                                        )
  feature_dict['macd_rule_0_30'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=0,
                                          days=30
                                        )
  feature_dict['macd_rule_1_18'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=1,
                                          days=18
                                        )
  feature_dict['macd_rule_1_24'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=1,
                                          days=24
                                        )
  feature_dict['macd_rule_1_30'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=1,
                                          days=30
                                        )
  feature_dict['macd_rule_2_18'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=2,
                                          days=18
                                        )
  feature_dict['macd_rule_2_24'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=2,
                                          days=24
                                        )
  feature_dict['macd_rule_2_30'] = apply_macd_rule(
                                          feature_dict['adj_close_features'],
                                          index=2,
                                          days=30
                                        )
  print 'Applying RSI rules'
  feature_dict['rsi_rule_8'] = apply_rsi_rule(
                                          feature_dict['adj_close_features'],
                                          days=8
                                        )
  feature_dict['rsi_rule_14'] = apply_rsi_rule(
                                          feature_dict['adj_close_features'],
                                          days=14
                                        )
  feature_dict['rsi_rule_20'] = apply_rsi_rule(
                                          feature_dict['adj_close_features'],
                                          days=20
                                        )
  print 'Applying stochastic rules'
  feature_dict['fast_stochastic_rule_12'] = apply_stoch_fast_rule(feature_dict, days=12)
  feature_dict['fast_stochastic_rule_18'] = apply_stoch_fast_rule(feature_dict, days=18)
  feature_dict['fast_stochastic_rule_24'] = apply_stoch_fast_rule(feature_dict, days=24)
  feature_dict['slow_stochastic_rule_12'] = apply_stoch_slow_rule(feature_dict, days=12)
  feature_dict['slow_stochastic_rule_18'] = apply_stoch_slow_rule(feature_dict, days=18)
  feature_dict['slow_stochastic_rule_24'] = apply_stoch_slow_rule(feature_dict, days=24)
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
