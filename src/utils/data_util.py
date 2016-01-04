#!/usr/bin/env python
from __future__ import division
import data.stock_data_store as sds, lib.talib as tl, numpy, sys, math, datetime
from pyalgotrade.dataseries import DataSeries
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar

def get_data(ticker, start_date=None, end_date=None):
  s = sds.StockDataStore()
  cursor = s.get_company_data(ticker, start_date, end_date)
  return [data for data in cursor]

def get_data_at_delta(delta, data, delta_label='date'):
  for i, dic in enumerate(data):
    if dic[delta_label] == delta:
      return dic
  return None
  
def get_snp_data_as_list(start, end):
  data_store = sds.StockDataStore()
  snp_data = data_store.get_company_data(
                            '^GSPC'
                            ,start_date=start
                            ,end_date=end
                          )
  datam = []
  for d in snp_data:
    datam.append(d)
  return datam

def align_data(d1, d2, delta_label='date'):
  small_d = []
  big_d = []
  is_d1_smalld = False
  
  if len(d1) == len(d2):
    return d1, d2
  elif len(d1) > len(d2):
    small_d = d2
    big_d = d1
  else:
    small_d = d1
    big_d = d2
    is_d1_smalld = True
    
  new_d =  []
  for data in small_d:
    dt = data[delta_label]
    new_d.append(get_data_at_delta(dt, big_d, delta_label))
  
  if is_d1_smalld:
    return d1, new_d 
  else:
    return new_d, d2

def get_ratio_for_key(t1, t2, key):
  t1_data = get_data(t1)
  t2_data = get_data(t2)
  if len(t1_data) != len(t2_data):
    t1_data, t2_data = remap_data(t1_data, t2_data) 
  return [t1_data[i][key] / t2_data[i][key] for i in range(len(t1_data))]

def get_ratio_for_key_with_date(t1, t2, key):
  t1_data = get_data(t1)
  t2_data = get_data(t2)
  if len(t1_data) != len(t2_data):
    t1_data, t2_data = remap_data(t1_data, t2_data) 
  d = []
  for i in range(len(t1_data)):
    d.append({'date':t1_data[i]['date'], 'ratio':(t1_data[i][key] / t2_data[i][key])})
  return d

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


class ArbiBar(bar.Bar):
  def __init__(self, datetime, open_, high, low, close, volume, adjClose, ratio):
    bar.Bar.__init__(self, datetime, open_, high, low, close, volume, adjClose)
    self.ratio = ratio

class ArbiParser(csvfeed.RowParser):
  def __init__(self, zone=0):
    self.__zone = zone
    self.__fields = []
  
  def getFieldNames(self):
    return self.__fields

  def getDelimitter(self):
    return None
  
  def parseBar(self, mongorow):
    openl = mongorow.pop('Open') if 'Open' in mongorow else 0.0
    high = mongorow.pop('High') if 'High' in mongorow else 0.0
    low =  mongorow.pop('Low') if 'Low' in mongorow else 0.0
    close =  mongorow.pop('Close') if 'Close' in mongorow else 0.0
    volume = mongorow.pop('Volume') if 'Volume' in mongorow else 0.0
    adj_close = mongorow.pop('Adj Clos') if 'Adj Clos' in mongorow else 0.0
    ratio = mongorow['ratio'] if 'ratio' in mongorow else None
    return ArbiBar(mongorow['date'], openl, high, 
                   low, close, volume, adj_close, 
                   ratio)
    
class ArbiFeed(csvfeed.BarFeed):
  def __init__(self, ftype='None'):
    csvfeed.BarFeed.__init__(self)
    self.f_type = ftype
    self.__bars = {}
    self.__nextBarIdx = {}
    self.__barFilter = None
  
  def addBarsFromCSV(self, data, instrument='None', row_parser=ArbiParser()):
    self.__bars.setdefault(instrument, [])
    self.__nextBarIdx.setdefault(instrument, 0)
    
    loaded_bars = []
    for datum in data:
      if self.__barFilter is None or self.__barFilter.includeBar(datum):
        row = row_parser.parseBar(datum)
        loaded_bars.append(row)
    self.__bars[instrument].extend(loaded_bars)
    barcmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
    self.__bars[instrument].sort(barcmp)
    self.registerInstrument(instrument)
  
  def getNextBars(self):
    # All bars must have the same datetime. We will return all the ones with the smallest datetime.
    smallestDateTime = None

    # Make a first pass to get the smallest datetime.
    for instrument, bars in self.__bars.iteritems():
      nextIdx = self.__nextBarIdx[instrument]
      if nextIdx < len(bars):
        if smallestDateTime == None or bars[nextIdx].getDateTime() < smallestDateTime:
          smallestDateTime = bars[nextIdx].getDateTime()

    if smallestDateTime == None:
      return None

    # Make a second pass to get all the bars that had the smallest datetime.
    ret = {}
    for instrument, bars in self.__bars.iteritems():
      nextIdx = self.__nextBarIdx[instrument]
      if nextIdx < len(bars) and bars[nextIdx].getDateTime() == smallestDateTime:
        ret[instrument] = bars[nextIdx]
        self.__nextBarIdx[instrument] += 1
    return bar.Bars(ret)
    

if __name__ == '__main__':
  #write_csv_file(sys.argv[1], sys.argv[2]) 
  a = ArbiFeed()
  d = get_ratio_for_key_with_date('TRNS', 'MAKO', 'Adj Clos')
  a.addBarsFromCSV(d)
  print dir(a.getNextBars().getBar('None'))