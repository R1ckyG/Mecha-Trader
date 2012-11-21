#!/usr/bin/env python
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np

class BuyAndHold(strategy.Strategy):
    def __init__(self, smaPeriod, f, tickers):
        strategy.Strategy.__init__(self, f, 15000)
        self.__position = {} 
        self.tickers = tickers
        self.result = None
            
    def onStart(self):
        print "Initial portfolio value: $%.2f" % self.getBroker().getCash()

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        position.setExitOnSessionClose(True)
        print "%s: BUY %d of %s at $%.2f" % (execInfo.getDateTime(), position.getQuantity(),
                                             position.getInstrument(), execInfo.getPrice())

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        print "%s: SELL %d of %s at $%.2f profit: %f" % (execInfo.getDateTime(), position.getQuantity(),
                                             position.getInstrument(), execInfo.getPrice(), position.getQuantity() * position.getNetProfit())
        #self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.exitPosition(self.__position)

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if len(self.__position) <= 0:
          for t in self.tickers:
            bar = bars.getBar(t)
            order = int(self.getBroker().getCash() / len(self.tickers))
            order = int(order / bar.getClose()) 
            self.__position[t] = self.enterLong(t, order, True)
    
    def onFinish(self, bars):
        self.result = self.getBroker().getValue(bars)
        print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)

def run_strategy(smaPeriod, tickers):
    # Load the yahoo feed from the CSV file

    f = du.ArbiFeed()
    for t in tickers:
      f.addBarsFromCSV(du.get_data(t), t)
    
    # Evaluate the strategy with the feed's bars.
    myStrategy = BuyAndHold(smaPeriod, f, tickers)
    plt = plotter.StrategyPlotter(myStrategy)
    for t in tickers:
      plt.getInstrumentSubplot(t).addDataSeries(t, f.getDataSeries(t))

    myStrategy.run()
    plt.plot()
if __name__ == '__main__':
  run_strategy(9, sys.argv[1:])
