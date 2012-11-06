#!/usr/bin/env python
import sys, matplotlib.pyplot as plt, lib.talib as tl, numpy as np
import utils.data_util as du

if __name__ == '__main__':
	if len(sys.argv) <= 2:
		print './bband_graph <ticker1> <ticker2>'
		sys.exit(1)
	ratios = du.get_ratio_for_key(sys.argv[1], sys.argv[2], 'Adj Clos')
	a, b, c = tl.BBANDS(np.array(ratios), timeperiod=20, nbdevup=2, 
                                     nbdevdn=2, matype=tl.MA_SMA) 
	plt.plot(ratios, 'g-.', label='Ratio')
	plt.plot(a, 'b--', label='Upper band')
	plt.plot(b, 'p--', label='Mean')
	plt.plot(c, 'r--', label='Lower band')
	plt.grid(True)
	plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.) 
	plt.show()