#!/usr/bin/env python
from pyalgotrade import bar, barfeed
from pyalgotrade.barfeed import csvfeed
from utils import data_util as du

class MongoBar(bar.Bar):
  def __init__(self, dateTime, open_, high, low, close, volume, adjClose, **kwargs):
    bar.Bar.__init__(self,dateTime, open_, high, low, close, volume, adjClose)
    self.ta = kwargs
  
class MongoRowParser(csvfeed.RowParser):
  def __init__(self, zone=0):
    self.__zone = zone
    self.__fields = []
  
  def getFieldNames(self):
    return self.__fields

  def getDelimitter(self):
    return None
  
  def parseBar(self, mongorow):
    date = mongorow.pop('date')
    openl = mongorow.pop('Open')
    high = mongorow.pop('High')
    low =  mongorow.pop('Low')
    close =  mongorow.pop('Close')
    volume = mongorow.pop('Volume')
    adj_close = mongorow.pop('Adj Clos')
    return MongoBar(date, openl, high, low, close, volume, adj_close, **mongorow)

class MongoFeed(csvfeed.BarFeed):
  def __init__(self):
    csvfeed.BarFeed.__init__(self)
    self.__bars = {}
    self.__nextBarIdx = {}
    self.__barFilter = None
  
  def addBarsFromCSV(self, instrument, row_parser):
    data = du.get_data(instrument)
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

if __name__ ==  '__main__':
  m = MongoFeed()
  m.addBarsFromCSV('GOOG', MongoRowParser())
  
