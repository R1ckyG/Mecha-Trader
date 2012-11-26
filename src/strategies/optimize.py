#!/usr/bin/env python
import sys, argparse 
import pair_trading, buy_and_hold, utils.data_util as du

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
  return parser

def getStrategy(type):
  if type.lower() == 'buy_and_hold':
    return buy_and_hold
  elif type.lower() == 'pair_trading':
    return pair_trading

class Optimizer:
  def __init__(self, strgy, tickers, lower=1, upper=100):
    self.lower = lower
    self.upper = upper
    self.strategy = strgy
    self.tickers = tickers
  
  def run(self):
    trials = []
    for i in range(self.lower, self.upper):
      try:
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
  opti = Optimizer(strat, args.tickers[0], args.lower_limit, args.upper_limit)
  t = opti.run()
  print t

