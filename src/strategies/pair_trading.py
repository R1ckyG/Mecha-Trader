#!/usr/bin/env python
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np

class PairStrategy(strategy.Strategy):
    def __init__(self, feed, smaPeriod, f, tick1, tick2):
        strategy.Strategy.__init__(self, f, 15000)
        self.__position = {} 
        self.__tick1 = tick1
        self.__tick2 = tick2
        self.pdata = feed.getDataSeries(tick1).getCloseDataSeries()
        self.result = None
        def get_ratio(bar):
          return bar.ratio
        self.ratios = f.getDataSeries('%s/%s' %(tick1, tick2))
        self.ratios = dataseries.BarValueDataSeries(f.getDataSeries('%s/%s' %(tick1, tick2)), get_ratio)
        self.ratio_series = du.RatioDataSeries(tick1, tick2, 'Adj Clos')
        a, b, c = du.run_command(
                      'BBANDS',
                      np.array(self.ratio_series.d), 
                      **{'timeperiod':smaPeriod, 'nbdevup':2, 'nbdevdn':2, 'matype':du.tl.MA_SMA}
                  )
        self.highs = dataseries.SequenceDataSeries([d for d in a.tolist()])
        #print [d for d in a.tolist()]
        self.mids = dataseries.SequenceDataSeries([d for d in b.tolist()])
        self.lows = dataseries.SequenceDataSeries([d for d in c.tolist()])
        """
        self.highs = du.ArbitraryDataSeries('Upper BBand', a.tolist())
        self.mids = du.ArbitraryDataSeries('Mean', b.tolist())
        self.lows = du.ArbitraryDataSeries('Lower BBand', c.tolist()) 
        """
        self.cross_below = cross.CrossBelow(self.ratios, self.lows)
        self.cross_above = cross.CrossAbove(self.ratios, self.highs)
      
            
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
        if self.cross_below is None:
            return
        bar = bars.getBar(self.__tick1)
        # If a position was not opened, check if we should enter a long position.
        if len(self.__position) == 0:
            if self.cross_below.getValue() > 0:
                order = int(.9 * (self.getBroker().getCash() / bar.getClose()))
                if self.__tick1 not in self.__position: self.__position[self.__tick1] = self.enterLong(self.__tick1, order, True)
        # Check if we have to exit the position.
        elif self.cross_above.getValue() > 0:   
            bar = bars.getBar(self.__tick2)
            order = int(.9 * (self.getBroker().getCash() / bar.getClose()))
            if self.__tick1 in self.__position:self.exitPosition(self.__position.pop(self.__tick1))
            if self.__tick2 not in self.__position:self.__position[self.__tick2] = self.enterLong(self.__tick2, order, True)
        elif self.cross_below.getValue() > 0:
            if self.__tick2 in self.__position:
            	print 'hello', bar.getDateTime()
            	self.exitPosition(self.__position.pop(self.__tick2))
            order = int(.9 * (self.getBroker().getCash() / bar.getClose()))
            if self.__tick1 not in self.__position:self.__position[self.__tick1] = self.enterLong(self.__tick1, order, True)
    
    def onFinish(self, bars):
       self.result = self.getBroker().getValue(bars) 
       print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)

def run_strategy(smaPeriod, tick, tick2='TRNS'):
    # Load the yahoo feed from the CSV file
    feed = mongofeed.MongoFeed()
    feed.addBarsFromCSV(tick, mongofeed.MongoRowParser())
    ratio = du.get_ratio_for_key_with_date(tick, tick2, 'Adj Clos')

    f = du.ArbiFeed()
    f.addBarsFromCSV(ratio, '%s/%s' %(tick, tick2))
    f.addBarsFromCSV(du.get_data(tick), tick)
    f.addBarsFromCSV(du.get_data(tick2), tick2)   
    
    # Evaluate the strategy with the feed's bars.
    myStrategy = PairStrategy(feed, smaPeriod, f, tick, tick2)
    plt = plotter.StrategyPlotter(myStrategy)
    plt.getInstrumentSubplot(tick).addDataSeries(tick, f.getDataSeries(tick))

    myStrategy.run()
    plt.plot()
if __name__ == '__main__':
  run_strategy(9, sys.argv[1], sys.argv[2])