#!/usr/bin/env python
import sys, datetime, pymongo
import YahooFinanceRetriever

START_DATE = '20091002'
STOCK_DB = 'stock_data'

class StockDataStore(object):
  def __init__(self, database=STOCK_DB):
    self.conn = pymongo.Connection()
    self.db = self.conn[database]
  
  def add_data(company, stock_data):
    collection = self.db[company]
    collection.insert(stock_data)
  
  def store(self, company, data):
    data_list = list()
    labels = data.pop(YahooFinanceRetriever.FEATURES)
    data_items = data.items()
    print 'labels: ', labels
    
    for datum in data_items:
      data_list.append(self.format(labels, company, datum))
      
    collection = self.db[company]
    collection.insert(data_list)
  
  def format(self, labels, company, data):
    new_data = dict()
    for i in range(1, len(labels)):
      new_data[labels[i]] = float(data[1][i - 1])
    new_data['ticker'] = company
    new_data['date'] = datetime.datetime.strptime(data[0], '%Y-%m-%d') 
    return new_data
  
  def fetch_and_store(self, company, start_date, end_date):
    data_fetcher = YahooFinanceRetriever.YahooFinanceRetriever()
    data = data_fetcher.get_data(company, start_date, end_date)
    self.store(company, data)
  
  def get_company_data(self, company, start_date=None, end_date=None):
    collection = self.db[company]
    start = None if start_date is None else start_date
    end = None if end_date is None else end_date
    data = None
    
    d = datetime.datetime.now()
    if start is None and end is None:
      data = collection.find().sort('date')
    elif start is None:
      data = collection.find({'date':{'$lte':end_date}}).sort('date')
    elif end is None:
      data = collection.find({'date':{'$gte':start_date}}).sort('date')
    else:
       data = collection.find({'$and':[{'date':{'$gte':start_date}},
                               {'date':{'$lte':end_date}}]}).sort('date')
    return data

  def batch_fetch(self, ticker_file, start_date=START_DATE):
    error_list = []
    f = open(ticker_file, 'r')
    for ticker in f:
      clean_ticker = ticker.strip()
      end_date = datetime.datetime.now().strftime('%Y%m%d')
      print 'Fetching data for %s from %s to %s'\
        % (clean_ticker, start_date, end_date)
      try:
        self.fetch_and_store(
                        clean_ticker, 
                        start_date, 
                        end_date
                      )
      except:
        error_list.append(ticker)
    print 'Failed tickers: %s' % '\n'.join(error_list)
    
  def save_data(self, ticker, data):
    collection = self.db[ticker]
    for datum in data:
      collection.save(datum)
  
if __name__ == '__main__':
  sd = StockDataStore()
  if len(sys.argv) > 1:
    sd.batch_fetch(sys.argv[1])
  else:
    sd.fetch_and_store('AAPL', '20100822','20120930')
