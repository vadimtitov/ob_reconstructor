import pandas as pd
from bisect import insort
from copy import copy
import sys
from functions import Reprinter, sound
reprinter = Reprinter()

import numpy as np

class LimitOrder:

    #Constructor
    def __init__(self, Timestamp, RecordType, Price, Volume, ID, Direction):
        self.Timestamp = Timestamp
        self.RecordType = RecordType
        self.Price = Price
        self.Volume = Volume
        self.ID = ID
        self.Direction = Direction

    #Signed price is needed to compare asks and bids: best bid is highest bid while best ask is the lowest ask.
    def signed_price(self):
        if self.Direction == 'B':
            return -self.Price
        else:
            return self.Price

    #'Greater than' operator
    def __gt__(self, other):

        if self.signed_price() > other.signed_price() :
            return True
        elif self.signed_price() == other.signed_price():
            if (self.Timestamp > other.Timestamp ):
                return True
        else:
            return False

    #'Equal' operator
    def __eq__(self, other):
        if (self.Price == other.Price) and (self.Timestamp == other.Timestamp):
            return True
        else:
            return False

    #'Less than' operator
    def __lt__(self, other):
        return not (self.__gt__(other) or self.__eq__(other))

    #print(LimitOrder_object) function
    def __str__(self):
        return('Timestamp |' + str(self.Timestamp)  + '\n' +
               'ID        |' + str(self.ID)         + '\n' +
               'RecordType|' + str(self.RecordType) + '\n' +
               'Price     |' + str(self.Price)      + '\n' +
               'Volume    |' + str(self.Volume)     + '\n' +
               'Direction |' + str(self.Direction)  + '\n')






class OrderBookPlus:

    #Constructor
    def __init__(self, recordEvents = False, recordOB= False):
        self.bids = []
        self.asks = []
        self.order_id = dict()
        self.recordEvents = recordEvents
        self.recordOB = recordOB
        self.history = []
        self.vwapSeries = dict()
        self.imbalanceSeries = dict()
        self.imbalanceSeries10 = dict()
        self.depthA = dict()
        self.depthB = dict()
        self.spoofer = dict()
        self.events = 'Timestamp, Event, Direction, OrderID, Price, Volume, Spoof\n'
        self.orderBookHistory = dict()

    def __recordEvent(self, order, eventType):
        if order.ID[0] == 's':
            spoof = 1
        else:
            spoof = 0
        self.events += '{},{},{},{},{},{},{}\n'.format(str(order.Timestamp), eventType,
                                                order.Direction, order.ID, order.Price,
                                                order.Volume, spoof)

    #OB records
    def __recordOB(self, time):
        self.orderBookHistory[time] = (self.asks, self.bids)


    #Checks if order can be instantly executed
    def __isMarketOrder(self, order, op_side):
        if order.Direction == 'A':                                #if it is ask order
            if op_side != [] and order.Price <= op_side[0].Price: #if opposite side(bids) is not empty and
                return True                                       #new ask < best bid

        else:                                                     #if it is buy order
            if op_side != [] and order.Price >= op_side[0].Price: #if opposite side(asks) is not empty and
                return True                                       #new bid > best ask

    #Member function for enter-type events
    def enter_order(self, new_order):
        new_order = copy(new_order)
        #record ENTER event
        if self.recordEvents == True:
            self.__recordEvent(new_order, 'ENTER')

        if new_order.Direction == 'A':                            #for asks this_side is asks and
            this_side = self.asks                                 #opposite_side is bids
            opposite_side = self.bids                             #vice versa for bids
        else:
            this_side = self.bids
            opposite_side = self.asks


        while new_order.Volume != 0:                                  #is new order volume(demand/supply) fullfilled ? ?
            if self.__isMarketOrder(new_order, opposite_side) == True:  #is it a market order ?
                best_opposite_quote = opposite_side[0]                #first element of the heap is the best quote


                if best_opposite_quote.Volume <= new_order.Volume:    #best_opposite_quote can't fullfill new_order?
                    new_order.Volume -= best_opposite_quote.Volume    #substract fullfilled part of volume
                    try:
                        del self.order_id[best_opposite_quote.ID]        #
                    except:
                        pass
                        #print('Order was not found in the order book')
                    del opposite_side[0]                              #remove executed order from the order book
                    ###FULL EXECUTION EVENT###
                    #if self.recordEvents == True:

                else:                                                 #best_opposite_quote can fullfill new_order
                    opposite_side[0].Volume -= new_order.Volume       #update best_opposite_quote volume
                    new_order.Volume = 0                              #new_order is fullfilled
                    self.order_id[best_opposite_quote.ID] = opposite_side[0] #update order_id dictionary
                    ###PARTIAL EXECUTION###
                    #if self.recordEvents == True:

            else:                                                     #it is a limit order
                insort(this_side, copy(new_order))                    #insort new_order to the order book using bisection method
                self.order_id[new_order.ID] = new_order               #add new order to order_id dictionary
                new_order.Volume = 0                                  #new_order is "fullfilled"
                ###ENTER EVENT###
                #if self.recordEvents == True:

            #Update back
            if new_order.Direction == 'A':
                self.asks = this_side
                self.bids = opposite_side
            else:
                self.bids = this_side
                self.asks = opposite_side


    #Member function for delete_type events
    def delete_order(self, id_to_delete):
        try:
            order_to_delete = self.order_id[id_to_delete] #this gives error if this order is not in order_id

            if order_to_delete.Direction == 'A':          #if order_to_delete is sell order
                self.asks.remove(order_to_delete)         #then remove it from asks
            else:                                         #if order_to_delete is
                self.bids.remove(order_to_delete)         #then remove it from bids


            del self.order_id[id_to_delete]               #remove order_to_delete from order_id
            ###CANCEL EVENT###
            if self.recordEvents == True:
                self.__recordEvent(order_to_delete, 'DELETE')

        except:
            pass
            #print('Order was not found in the Order Book: cannot be deleted or amended')



    #Member function for amend-type events
    def amend_order(self, order_to_amend):
        self.delete_order(order_to_amend.ID)              #Amend means delete old and then
        self.enter_order(order_to_amend)                  #enter new

    #Member function that updates order book for event of any of 3 types and then records order book state variables

    def add(self, new_order):                                                   #(mid price, quote, volumes)
        if len(self.asks) < 3 or len(self.bids) < 3:
            sound()
        if new_order.RecordType == 'ENTER':
            self.enter_order(new_order)
        elif new_order.RecordType == 'DELETE':
            self.delete_order(new_order.ID)
        elif new_order.RecordType == 'AMEND':
            self.amend_order(new_order)

        #RECORD TO OB-HISTORY VARIABLE
        if self.recordOB == True: self.__recordOB(new_order.Timestamp)


        #Record results
        try:
            self.history.append( [ new_order.Timestamp,
                                   self.bids[0].Volume,
                                   self.bids[0].Price,
                                   self.asks[0].Price,
                                   self.asks[0].Volume  ] )
            #self.vwapSeries[new_order.Timestamp] = self.__VWAP()
            self.imbalanceSeries[new_order.Timestamp] = self.imbalance()
            self.imbalanceSeries10[new_order.Timestamp] = self.imbalanceOfDepth(10)
            #self.depthA[new_order.Timestamp] = len(self.asks)
            #self.depthB[new_order.Timestamp] = len(self.bids)
        except:                                         #At the very beginning of reconstruction asks or bids
            pass                                        #heaps may be empty, so, there is nothing to append






    #Getters
    def getQuotes(self):
        quotes = pd.DataFrame(self.history, columns= ['Timestamp','Bid Volume', 'Best Bid', 'Best Ask', 'Ask Volume'])
        return quotes.set_index('Timestamp')

    def getMidPrices(self):
        a = self.getQuotes()['Best Ask']
        b = self.getQuotes()['Best Bid']
        return (a + b)/2

    def getSpread(self):
        a = self.getQuotes()['Best Ask']
        b =  self.getQuotes()['Best Bid']
        return (a-b)/a

    def getImbalance(self):
        return pd.Series(self.imbalanceSeries)

    def getImbalance10(self):
        return pd.Series(self.imbalanceSeries10)

    def getVWAP(self):
        return pd.Series(self.vwapSeries)


    def __pickPrices(self, orders, n = 10):
        if len(orders) == 0:
            return ['        ']*n
        elif len(orders) >= n:
            return [str(round(order.Price,4)) for order in orders[0:n]]
        else:
            result = [str(round(order.Price,4)) for order in orders]
            result += ['    ']*(len(orders)-n)
            return result


    def __pickVolumes(self, orders, n = 10):
        if len(orders) == 0:
            return ['        ']*n
        elif len(orders) >= n:
            return [str(order.Volume) for order in orders[0:n]]
        else:
            return [str(order.Volume) for order in orders] + ['    ']*(len(orders)-n)


    def __pickIDs(self, orders, n = 10):
        if len(orders) == 0:
            return ['        ']*n
        elif len(orders) >= n:
            return [str(order.ID) for order in orders[0:n]]
        else:
            return [str(order.ID) for order in orders] + ['    ']*(len(orders)-n)

    def __VWAP(self):
        ob = self.asks + self.bids
        return sum([order.Price*order.Volume for order in ob])/\
                sum([order.Volume for order in ob])

    def imbalance(self):
        a = sum([order.Volume for order in self.asks])
        b = sum([order.Volume for order in self.bids])
        return a/(a+b)

    def imbalanceOfDepth(self, depth = 10):
        if len(self.asks) <= depth:
            a = sum(order.Volume for order in self.asks)
        else:
            a = sum(order.Volume for order in self.asks[0:depth])
        if len(self.bids) <= depth:
            b = sum(order.Volume for order in self.bids)
        else:
            b = sum(order.Volume for order in self.bids[0:depth])
        return a/(a+b)

    def currentMP(self):
        try:
            return (self.asks[0].Price + self.bids[0].Price)/2
        except IndexError:
            try:
                return self.asks[0].Price
            except IndexError:
                try:
                    return self.bids[0].Price
                except IndexError:
                    return 0

    def getOBwithIDs(self):
        asks = self.__pickPrices(self.asks)
        bids = self.__pickPrices(self.bids)
        askV = self.__pickVolumes(self.asks)
        bidV = self.__pickVolumes(self.bids)
        askID = self.__pickIDs(self.asks)
        bidID = self.__pickIDs(self.bids)

        toPrint = \
            '       Price   Volume   OrderID'  + '\n' + \
            'Asks: {}   {}    {}'.format(asks[9], askV[9], askID[9]) + '\n' + \
            '      {}   {}    {}'.format(asks[8], askV[8], askID[8]) + '\n' + \
            '      {}   {}    {}'.format(asks[7], askV[7], askID[7]) + '\n' + \
            '      {}   {}    {}'.format(asks[6], askV[6], askID[6]) + '\n' + \
            '      {}   {}    {}'.format(asks[5], askV[5], askID[5]) + '\n' + \
            '      {}   {}    {}'.format(asks[4], askV[4], askID[4]) + '\n' + \
            '      {}   {}    {}'.format(asks[3], askV[3], askID[3]) + '\n' + \
            '      {}   {}    {}'.format(asks[2], askV[2], askID[2]) + '\n' + \
            '      {}   {}    {}'.format(asks[1], askV[1], askID[1]) + '\n' + \
            '      {}   {}    {}'.format(asks[0], askV[0], askID[0]) + '\n' + \
            '____________________________'                           + '\n' + \
            '              ' + '\n' + \
            'Bids: {}   {}    {}'.format(bids[0], bidV[0], bidID[0]) + '\n' + \
            '      {}   {}    {}'.format(bids[1], bidV[1], bidID[1]) + '\n' + \
            '      {}   {}    {}'.format(bids[2], bidV[2], bidID[2]) + '\n' + \
            '      {}   {}    {}'.format(bids[3], bidV[3], bidID[3]) + '\n' + \
            '      {}   {}    {}'.format(bids[4], bidV[4], bidID[4]) + '\n' + \
            '      {}   {}    {}'.format(bids[5], bidV[5], bidID[5]) + '\n' + \
            '      {}   {}    {}'.format(bids[6], bidV[6], bidID[6]) + '\n' + \
            '      {}   {}    {}'.format(bids[7], bidV[7], bidID[7]) + '\n' + \
            '      {}   {}    {}'.format(bids[8], bidV[8], bidID[8]) + '\n' + \
            '      {}   {}    {}'.format(bids[9], bidV[9], bidID[9]) + '\n'

        return toPrint


    def printOBwithIDs(self, progress):
        toPrint = self.getOBwithIDs()
        reprinter.reprint(text = toPrint)


    def printOB(self, progress):

        asks = self.__pickPrices(self.asks,10)
        bids = self.__pickPrices(self.bids,10)
        askV = self.__pickVolumes(self.asks,10)
        bidV = self.__pickVolumes(self.bids,10)

        toPrint = \
            'Progress: {}% '.format(progress) +'\n'   +'\n' +\
            'Asks: {}   {} '.format(asks[9], askV[9]) +'\n' +\
            '({})  {}   {} '.format(len(asks), asks[8], askV[8]) +'\n' +\
            '      {}   {} '.format(asks[7], askV[7]) +'\n' +\
            '      {}   {} '.format(asks[6], askV[6]) +'\n' +\
            '      {}   {} '.format(asks[5], askV[5]) +'\n' +\
            '      {}   {} '.format(asks[4], askV[4]) +'\n' +\
            '      {}   {} '.format(asks[3], askV[3]) +'\n' +\
            '      {}   {} '.format(asks[2], askV[2]) +'\n' +\
            '      {}   {} '.format(asks[1], askV[1]) +'\n' +\
            '      {}   {} '.format(asks[0], askV[0]) +'\n' +\
            '________________________'                 +'\n' +\
            '              '                           +'\n' +\
            'Bids: {}   {} '.format(bids[0], bidV[0]) +'\n' +\
            '({})  {}   {} '.format(len(bids), bids[1], bidV[1]) +'\n' +\
            '      {}   {} '.format(bids[2], bidV[2]) +'\n' +\
            '      {}   {} '.format(bids[3], bidV[3]) +'\n' +\
            '      {}   {} '.format(bids[4], bidV[4]) +'\n' +\
            '      {}   {} '.format(bids[5], bidV[5]) +'\n' +\
            '      {}   {} '.format(bids[6], bidV[6]) +'\n' +\
            '      {}   {} '.format(bids[7], bidV[7]) +'\n' +\
            '      {}   {} '.format(bids[8], bidV[8]) +'\n' +\
            '      {}   {} '.format(bids[9], bidV[9]) +'\n'


        reprinter.reprint(text = toPrint)
