#!/usr/bin/env python

from __future__ import division
import urllib
import ystockquote

FEATURES = 'labels'

def main():
	feature_retriever = YahooFinanceRetriever()
	print feature_retriever.get_data_for_day('^GSPC', '20110822' )
	print feature_retriever.get_data('^GSPC', '20100822','20110822')

class YahooFinanceRetriever(object):
	"""Python module for retrieving data from yahoo finance"""
	def __init__(self):
		return 
			
	def get_data(self, comp, start_date, end_date):
		feature_dict = {}
		results = ystockquote.get_historical_prices(comp ,start_date, end_date)
		feature_dict[FEATURES] = results.pop(0)
		for quotes in results:
			key = quotes.pop(0)
			feature_dict[key] = quotes
		return feature_dict
		
	def get_data_for_day(self, comp, date):
		return self.get_data(comp, date, date)
	
if __name__=="__main__":
	main()		

		