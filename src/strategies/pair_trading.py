#!/usr/bin/env python
from pyalgotrade import strategy, dataseries, plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma, cross, trend
from data import mongofeed
from pyalgotrade.dataseries import BarValueDataSeries
from utils import data_util as du
import sys, numpy as np
from analysis import metric

metrics = metric.Metrics()

class PairStrategy(strategy.Strategy):
    def __init__(self, feed, smaPeriod, f, tick1, tick2):
        strategy.Strategy.__init__(self, f, 15000)
        self.__position = {} 
        self.__tick1 = tick1
        self.__tick2 = tick2
        self.pdata = feed.getDataSeries(tick1).getCloseDataSeries()
        self.result = None
        self.last_price = {}
        self.last_price.setdefault(tick1, None)
        self.last_price.setdefault(tick2, None)
        
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
        self.cautious_cross_below = cross.CrossBelow(self.ratios, self.highs)
        self.cautious_cross_above = cross.CrossAbove(self.ratios, self.highs)
        self.price_slope = trend.Slope(self.ratios, smaPeriod)
        self.last_slope = 0
      
            
    def onStart(self):
        metrics.init_balance = self.getBroker().getCash()
        print "Initial portfolio value: $%.2f" % self.getBroker().getCash()

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        #position.setExitOnSessionClose(True)
        print "%s: BUY %d of %s at $%.2f slope: %f" % (execInfo.getDateTime(), position.getQuantity(),
                                             position.getInstrument(), execInfo.getPrice(), self.last_slope)

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        net_profit = position.getResult()
        inst = position.getInstrument()
        date = execInfo.getDateTime()
        if net_profit > 0:
          metrics.log_pos_returns(inst, date, net_profit)
        else:
          metrics.log_neg_returns(inst, date, net_profit)
        print "%s: SELL %d of %s at $%.2f profit: %f slope: %f" % (execInfo.getDateTime(), position.getQuantity(),
                                             position.getInstrument(), execInfo.getPrice(), position.getQuantity() * position.getNetProfit()
                                             ,self.last_slope)
        #self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.exitPosition(self.__position)

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if self.cross_below is None:
            return
        metrics.extend_period()
        self.last_slope = self.price_slope.getValue()
        bar = bars.getBar(self.__tick1)
        bar2 = bars.getBar(self.__tick2)
        
        if self.last_price[self.__tick1]:
          roc = (bar.getClose() - self.last_price[self.__tick1]) / self.last_price[self.__tick1]
          metrics.log_day_roc(self.__tick1, roc)  
        if self.last_price[self.__tick2]:
          roc = (bar2.getClose() - self.last_price[self.__tick2]) / self.last_price[self.__tick2]
          metrics.log_day_roc(self.__tick2, roc) 
        self.last_price[self.__tick1] = bar.getClose()
        self.last_price[self.__tick2] = bar2.getClose()   
        
        # If a position was not opened, check if we should enter a long position.
        if len(self.__position) == 0:
            if self.cross_below.getValue() > 0:
                order = int(.9 * (self.getBroker().getCash() / bar.getClose()))
                if self.__tick1 not in self.__position: self.__position[self.__tick1] = self.enterLong(self.__tick1, order, True)
        # Check if we have to exit the position.
        elif self.cross_above.getValue() > 0:   
            order = int(.9 * (self.getBroker().getCash() / bar2.getClose()))
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
       metrics.final_balance = self.result 
       print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)

def run_strategy(smaPeriod, tick, tick2='TRNS', plot=True):
    # Load the yahoo feed from the CSV file
    plt = None
    feed = mongofeed.MongoFeed()
    feed.addBarsFromCSV(tick, mongofeed.MongoRowParser())
    ratio = du.get_ratio_for_key_with_date(tick, tick2, 'Adj Clos')

    f = du.ArbiFeed()
    f.addBarsFromCSV(ratio, '%s/%s' %(tick, tick2))
    data = du.get_data(tick)
    
    max_date = min_date = None
    if max_date == None:
      max_date = data[-1]['date']
    elif max_date < data[-1]['date']:
      max_date = data[-1]['date']

    if min_date == None:
      min_date = data[0]['date']
    elif min_date > data[0]['date']:
      min_date = data[0]['date']   
    f.addBarsFromCSV(data, tick)
    
    data = du.get_data(tick2)
    if max_date == None:
      max_date = data[-1]['date']
    elif max_date < data[-1]['date']:
      max_date = data[-1]['date']

    if min_date == None:
      min_date = data[0]['date']
    elif min_date > data[0]['date']:
      min_date = data[0]['date'] 
    f.addBarsFromCSV(data, tick2)   
    
    print 'start: %r end: %r' %(min_date, max_date)
    metrics.start_date = min_date
    metrics.end_date = max_date
    
    # Evaluate the strategy with the feed's bars.
    myStrategy = PairStrategy(feed, smaPeriod, f, tick, tick2)
    if plot:plt = plotter.StrategyPlotter(myStrategy)
    if plot:plt.getInstrumentSubplot(tick).addDataSeries(tick, f.getDataSeries(tick))

    myStrategy.run()
    dd = metrics.get_all_drawdown()
    winners = metrics.get_all_win()
    losers = metrics.get_all_losses()
    avg_gain = metrics.get_all_gain()
    avg_losses = metrics.get_all_avglosses()
    returns = metrics.get_portfolio_annualized_returns()
    metrics.build_comp_report('%s-%s-pair_trading.txt' % (tick, tick2))
    print 'drawdown: \n%r' % (dd), 'Win percentage: \n%r ' % (winners), 'Loss perc.: \n%r' % (losers)
    print 'Gains: \n%r' % (avg_gain), 'Losses: \n%r' % (avg_losses)
    print 'Returns: %f' % (returns)
    if plot:plt.plot()
    
    return myStrategy.result

if __name__ == '__main__':
  run_strategy(int(sys.argv[3]), sys.argv[1], sys.argv[2])
