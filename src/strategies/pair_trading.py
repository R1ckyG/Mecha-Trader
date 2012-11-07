from pyalgotrade import strategy, dataseries
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from data import mongofeed
from utils import data_util as du
import sys, numpy as np

class PairStrategy(strategy.Strategy):
    def __init__(self, feed, smaPeriod, tick1, tick2):
        strategy.Strategy.__init__(self, feed, 100000)
        self.__position = None
        self.__tick1 = tick1
        self.__tick2 = tick2
        self.pdata = feed.getDataSeries(tick1).getCloseDataSeries()
        self.ratios = dataseries.SequenceDataSeries(du.get_ratio_for_key(tick1, tick2, 'Adj Clos'))
        self.ratio_series = du.RatioDataSeries(tick1, tick2, 'Adj Clos')
        a, b, c = du.run_command(
                      'BBANDS',
                      np.array(self.ratio_series.d), 
                      **{'timeperiod':smaPeriod, 'nbdevup':2, 'nbdevdn':2, 'matype':du.tl.MA_SMA}
                  )
        self.highs = dataseries.SequenceDataSeries([d for d in a.tolist()])
        print [d for d in a.tolist()]
        self.mids = dataseries.SequenceDataSeries([d for d in b.tolist()])
        self.lows = dataseries.SequenceDataSeries([d for d in c.tolist()])
        """
        self.highs = du.ArbitraryDataSeries('Upper BBand', a.tolist())
        self.mids = du.ArbitraryDataSeries('Mean', b.tolist())
        self.lows = du.ArbitraryDataSeries('Lower BBand', c.tolist()) 
        """
        self.cross_below = cross.CrossAbove(self.pdata, self.highs)
        self.cross_above = cross.CrossBelow(self.ratios, self.mids)
      
            
    def onStart(self):
        print "Initial portfolio value: $%.2f" % self.getBroker().getCash()

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        print "%s: BUY at $%.2f" % (execInfo.getDateTime(), execInfo.getPrice())

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        print "%s: SELL at $%.2f" % (execInfo.getDateTime(), execInfo.getPrice())
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.exitPosition(self.__position)

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if self.cross_below is None:
            return
        bar = bars.getBar(self.__tick1)
        # If a position was not opened, check if we should enter a long position.
        if self.__position == None:
            print 'Inside'
            if self.cross_below.getValue()  > 0:
                print 'More Inside'
                # Enter a buy market order for 10 orcl shares. The order is good till canceled.
                self.__position = self.enterLong(self.__tick1, 10, True)
        # Check if we have to exit the position.
        elif self.cross_above.getValue()  > 0:
             self.exitPosition(self.__position)

    def onFinish(self, bars):
        print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)

def run_strategy(smaPeriod, tick, tick2='TRNS'):
    # Load the yahoo feed from the CSV file
    feed = mongofeed.MongoFeed()
    feed.addBarsFromCSV(tick, mongofeed.MongoRowParser())

    # Evaluate the strategy with the feed's bars.
    myStrategy = PairStrategy(feed, smaPeriod, tick, 'TRNS')
    myStrategy.run()

run_strategy(15, sys.argv[1])