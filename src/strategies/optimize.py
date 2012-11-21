#!/usr/bin/env python
import sys, argparse 
import pair_trading, buy_and_hold, utils.data_util as du

def get_argument_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--strategy', help='Strategy class to run', 
                    dest='strategy', default='buy_and_hold', action='store')
  parser.add_argument('-l', '--lower-limit', help='Lower bound for period variable',
                    dest='lower_limit', default=1, action='store')
  parser.add_argument('-u', '--upper-limit', help='Upper bound for period variable',
                    dest='upper_limit', default=100, action='store')
  parser.add_argument('-t', '--tickers', help='Tickers for companies to run separated by space',
                    dest='tickers', nargs='*', action='append')
  return parser

if __name__ =='__main__':
  parser = get_argument_parser()
  args= parser.parse_args()
  print args

