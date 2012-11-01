from __future__ import division
import data.stock_data_store as sds, lib.talib as tl, numpy
def get_data(ticker):
  s = sds.StockDataStore()
  cursor = s.get_company_data(ticker)
  return [data for data in cursor]

def get_ratio_for_key(t1, t2, key):
  t1_data = get_data(t1)
  t2_data = get_data(t2)
  if len(t1_data) != len(t2_data):
    t1_data, t2_data = remap_data(t1_data, t2_data) 
    print len(t1_data), len(t2_data)
  return [t1_data[i][key] / t2_data[i][key] for i in range(len(t1_data))]

def remap_data(d1, d2):
  print len(d1), len(d2)
  len1 = len(d1)
  len2 = len(d2)
  if len1 == len2:
    return d1, d2
  m = max(len1, len2)
  if m == len1:
    return d1[len1 - len2:], d2
  else:
    return d1, d2[len2 - len1:]

def run_command(command, data):
  args, varargs, varkw, defaults = inspect.getargspec(func)
  if defaults:
    args=args[:-length]
  if hasattr(tl, command):
    f =  getattr(tl, command)
    if isinstance(data, list):
      data = numpy.array(data)
    return f(data)
  return None

def get_feature_data(ticker, feature):
  d = get_data(ticker)
  return [data[feature] for data in d]
