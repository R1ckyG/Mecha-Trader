#!/usr/bin/env python
import sys, argparse 
import pair_trading, buy_and_hold, trending
import utils.data_util as du

def get_argument_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--strategy', help='Strategy class to run', 
                    dest='strategy', default='buy_and_hold', action='store')
  parser.add_argument('-l', '--lower-limit', help='Lower bound for period variable',
                    dest='lower_limit', default=3, action='store')
  parser.add_argument('-u', '--upper-limit', help='Upper bound for period variable',
                    dest='upper_limit', default=100, action='store')
  parser.add_argument('-t', '--tickers', help='Tickers for companies to run separated by space',
                    dest='tickers', nargs='*', action='append')
  parser.add_argument('-f', '--file', help='File',dest='tfile',  action='store')
  return parser

def getStrategy(type):
  if type.lower() == 'buy_and_hold':
    return buy_and_hold
  elif type.lower() == 'pair_trading':
    return pair_trading
  elif type.lower() == 'trending':
    return trending

class Optimizer:
  def __init__(self, strgy, tickers, lower=1, upper=100):
    self.lower = int(lower)
    self.upper = int(upper)
    self.strategy = strgy
    self.tickers = tickers
  
  def run(self):
    trials = []
    for i in range(self.lower, self.upper):
      print (25 * '--') + ('Running trial for %d period' % i) + (25 * '--')
      try:
        if self.strategy == trending:
          strat = self.strategy.run_strategy(i, self.tickers, plot=False)
        else:
          strat = self.strategy.run_strategy(i, *self.tickers, plot=False)
        trials.append((strat, i))
      except Exception, e:
        print e, self.tickers, i
    return sorted(trials)

if __name__ =='__main__':
  parser = get_argument_parser()
  args = parser.parse_args()
  print args, args.strategy
  strat = getStrategy(args.strategy)
  tickers = None
  if args.tfile:
    f = open(args.tfile, 'r')
    tickers = [line.strip() for line in f]
  else:
    tickers = args.tickers[0]
  opti = Optimizer(strat, tickers, args.lower_limit, args.upper_limit)
  t = opti.run()
  print t

