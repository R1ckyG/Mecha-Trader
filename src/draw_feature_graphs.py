#!/usr/bin/env python
import sys
from matplotlib import pyplot as plt
from stock_data_store import StockDataStore as sds

def draw_plots_for_features(ticker, features):
  results = {}
  data_store = sds()

  for feature in features:
    results[feature] = list()
  data = data_store.get_company_data(ticker)
  for d in data:
    for f in features:
      try:
        results[f].append(d[f])
      except:
        pass
  for i in range(len(features)):
    print features[i]
    plt.subplot(int('%d1%d' % (len(features), i+1)))
    plt.plot(results[features[i]])
  plt.show()

if __name__ == '__main__':
  print sys.argv
  draw_plots_for_features(sys.argv[1], sys.argv[2:])
