#!/usr/bin/env python
from __future__ import division
import data.stock_data_store as sds, lib.talib as tl, numpy, sys, math
from pyalgotrade.dataseries import DataSeries

def get_data(ticker):
  s = sds.StockDataStore()
  cursor = s.get_company_data(ticker)
  return [data for data in cursor]

def get_ratio_for_key(t1, t2, key):
  t1_data = get_data(t1)
  t2_data = get_data(t2)
  if len(t1_data) != len(t2_data):
    t1_data, t2_data = remap_data(t1_data, t2_data) 
  return [t1_data[i][key] / t2_data[i][key] for i in range(len(t1_data))]

def remap_data(d1, d2):
  len1 = len(d1)
  len2 = len(d2)
  if len1 == len2:
    return d1, d2
  m = max(len1, len2)
  if m == len1:
    return d1[len1 - len2:], d2
  else:
    return d1, d2[len2 - len1:]

def run_command(command, data, **kwargs):
  if hasattr(tl, command):
    f =  getattr(tl, command)
    if isinstance(data, list):
      data = numpy.array(data)
    return f(data, **kwargs)
  return None

def get_feature_data(ticker, feature):
  d = get_data(ticker)
  return [data[feature] for data in d]


def dict_to_row(d):
	row = ''
	for key in d:
		row = row + '%s, ' % str(d[key])
	return row

def write_csv_file(t, filename):
	data = get_data(t)
	output = open(filename, 'w')
	output.write('%s\n' % ', '.join(data[0].keys()))
	for d in data:
		output.write("%s\n" % dict_to_row(d))
	output.close()

class ArbitraryDataSeries(DataSeries): 
  def __init__(self, desc, data):
    self.d = data
    self.desc = desc
  
  def getFirstValidPos(self):
    i = 0
    for d in self.d:
      if math.isnan(d):
        i = i + 1
        continue
      return i
    return None
  
  def getLength(self):
    return len(self.d)
  
  def getValueAbsolute(self, pos):
    return self.d[pos]  

class FeatureDataSeries(DataSeries): 
  def __init__(self, ticker, feature):
    self.d = get_feature_data(ticker, feature)
    self.ticker = ticker
    self.feature = feature
    self.firstvalid = None
  
  def getFirstValidPos(self):
    i = 0
    for d in self.d:
      if math.isnan(d):
        i = i + 1
        continue
      return i
    return None
  
  def getLength(self):
    return len(self.d)
  
  def getValueAbsolute(self, pos):
    return self.d[pos]    

class RatioDataSeries(DataSeries): 
  def __init__(self, ticker, ticker2, feature):
    self.d = get_ratio_for_key(ticker, ticker2, feature)
    self.ticker = ticker
    self.ticker2 = ticker2
    self.feature = feature

  def getFirstValidPos(self):
    i = 0
    for d in self.d:
      if math.isnan(d):
        i = i + 1
        continue
      return i
    return None

  def getLength(self):
    return len(self.d)

  def getValueAbsolute(self, pos):
		# Check that there are enough values to calculate this (given the current window size and the nested ones).
		print 'say what'
		if pos < self.getFirstValidPos() or pos >= self.getLength():
			return None
 
		# Check that we have enough values to use
		firstPos = pos - self.__windowSize + 1
		assert(firstPos >= 0)
 
		# Try to get the value from the cache.
		ret = self.d[pos]
		# Avoid caching None's in case a invalid pos is requested that becomes valid in the future.
		return ret

if __name__ == '__main__':
	write_csv_file(sys.argv[1], sys.argv[2])	
	