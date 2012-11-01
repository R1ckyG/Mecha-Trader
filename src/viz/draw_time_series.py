#!/usr/bin/env python
import sys, datetime,  matplotlib as mpl
from matplotlib import pyplot as plt
from data.stock_data_store import StockDataStore as sds
import analysis.find_correlations as fc

def draw_viz(t1, t2):
  data_store = sds()
  delta = datetime.timedelta(days=1)
    
  t1_data = []
  t2_data = []
  dates = []
   
  d_cursor = data_store.get_company_data(t1)
  for d in d_cursor:
    t1_data.append(d['Adj Clos'])
    dates.append(d['date'])
  d_cursor = data_store.get_company_data(t2)
  for d in d_cursor:
    t2_data.append(d['Adj Clos'])  
  print len(t1_data), len(t2_data)
  p, sprd, beta = fc.get_adf(t1, t2, spread=True)
  dates = mpl.dates.date2num(dates)
  p1 = plt.plot_date(dates, sprd, 'b-.', label='Sprd') 
  p2 = plt.plot_date(dates, t1_data, 'g-.', label=t1) 
  p3 = plt.plot_date(dates, t2_data, 'r-.', label=t2) 
  plt.grid(True)
  plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.) 
  def add_vert_line(event):
    plt.avspan(event.xdata, event.xdata, ls='p-')
  print 'Beta: %f' % beta
  plt.show() 
  
if __name__ =='__main__':
  if len(sys.argv) < 3:
    print 'Error: ./draw_time_series ticker1 ticker2'
  else:
    draw_viz(sys.argv[1], sys.argv[2])
