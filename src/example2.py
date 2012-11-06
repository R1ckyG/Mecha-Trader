from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from data import mongofeed
import sys

class MyStrategy(strategy.Strategy):
    def __init__(self, feed, smaPeriod, tick):
        strategy.Strategy.__init__(self, feed, 100000)
        self.__sma = ma.SMA(feed.getDataSeries(tick).getCloseDataSeries(), smaPeriod)
        self.__position = None
        self.__tick = tick

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
        if self.__sma.getValue() is None:
            return

        bar = bars.getBar(self.__tick)
        # If a position was not opened, check if we should enter a long position.
        if self.__position == None:
            if bar.getClose() > self.__sma.getValue():
                # Enter a buy market order for 10 orcl shares. The order is good till canceled.
                self.__position = self.enterLong(self.__tick, 10, True)
        # Check if we have to exit the position.
        elif bar.getClose() < self.__sma.getValue():
             self.exitPosition(self.__position)

    def onFinish(self, bars):
        print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)

def run_strategy(smaPeriod, tick):
    # Load the yahoo feed from the CSV file
    feed = mongofeed.MongoFeed()
    feed.addBarsFromCSV(tick, mongofeed.MongoRowParser())

    # Evaluate the strategy with the feed's bars.
    myStrategy = MyStrategy(feed, smaPeriod, tick)
    myStrategy.run()

run_strategy(15, sys.argv[1])