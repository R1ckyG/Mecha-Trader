#!/usr/bin/env python
import sys, random

if __name__ == '__main__':
  f = open(sys.argv[1], 'r')
  out_file = open('random_tickers.txt', 'w')
  percent = float(sys.argv[2])
  for line in f:
    if random.random() < percent:
      out_file.write('%s\n' % line.strip())
  f.close()
  out_file.close()
