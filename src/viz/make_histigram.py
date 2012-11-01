#!/usr/bin/env python
import sys, operator
from matplotlib import pyplot as plt

if __name__ == '__main__':
  f = open(sys.argv[1], 'r')
  contents = [line.split(',') for line in f]
  f.close()
  histigram = dict() 
  contents = filter(lambda x: True if x[2].strip() =='True' else False, contents)
  for line in contents:
    tickers = line[0].split('/')
    count =  1 if tickers[0] not in histigram else histigram[tickers[0]][0] +1
    s = set() if tickers[0] not in histigram else histigram[tickers[0]][1]
    s.add(tickers[1])
    histigram[tickers[0]] = ( count, s)
  histigram = histigram.items()
  #histigram = sorted(histigram, key=operator.itemgetter(1))
  histi_data = []
  labels = []
  for ticker in histigram:
    histi_data.append(ticker[1][0])
    labels.append(ticker[0])
    print '%s: %d %s' % (ticker[0], ticker[1][0],ticker[1][1])
  fig, ax = plt.subplots()
  plt.bar(range(len(histi_data)), histi_data, color='green')
  ax.set_xticks(range(len(histi_data)))
  ax.set_xticklabels(labels)
  plt.grid(True)
  plt.show()
  
