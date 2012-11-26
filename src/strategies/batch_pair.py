#!/usr/bin/env python
import sys, pair_trading, optimize

if __name__ == '__main__':
  f = open(sys.argv[1], 'r')
  data = [line.split(',') for line in f]
  data = filter(lambda x: x[2].strip() == 'True', data)
  results = []
  print len(data)
  for d in data:
    o = optimize.Optimizer(pair_trading, d[0].split('/'), 3, 10)
    t = o.run()
    if len(t) > 0 and len(d) > 0: results.append((t[-1], d[0]))
  print sorted(results)
  out = open('batch_out.txt', 'w')
  results = sorted(results)
  for r in results:
    out.write('%r, %r\n' % r)
  out.close()

