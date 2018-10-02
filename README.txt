1. To use reconstructor convert list of events to the list of LimitOrder objects
2. Create OrderBook object
3. Iterate over list of LimitOrder objects calling .add(LimitOrderObject) at each iteration 
4. After reconstruction is finished use OrderBook method functions to extract needed data

____________Pseudo_code____________

list = [LimitOrder(event) for event in events]
ob = OrderBook()
for x in list:
    ob.add(x)

ob.getMP('1s').plot() # plot mid prices after reconstruction

