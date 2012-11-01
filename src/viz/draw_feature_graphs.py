#!/usr/bin/env python
import sys, datetime, matplotlib
from matplotlib import pyplot as plt
from data.stock_data_store import StockDataStore as sds

def draw_plots_for_features(ticker, features):
  results = {}
  data_store = sds()
  delta = datetime.timedelta(days=1)
  
  for feature in features:
    results[feature] = list()
  data = data_store.get_company_data(ticker)
  dates = []
  for d in data:
    dates.append(d['date'])
    for f in features:
      try:
        results[f].append(d[f])
      except:
        pass
  
  dates = matplotlib.dates.date2num(dates)
  for i in range(len(features)):
    print features[i]
    plt.subplot(int('%d1%d' % (len(features), i+1)))
    print len(dates), len(results[features[i]])
    plt.plot_date(dates ,results[features[i]], 'r-.')
  plt.grid(True)
  plt.show()

if __name__ == '__main__':
  print sys.argv
  draw_plots_for_features(sys.argv[1], sys.argv[2:])
