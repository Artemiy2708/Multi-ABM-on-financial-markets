from typing import List, Optional

from AgentBasedModel.utils import Order, OrderList, logging
from AgentBasedModel.utils.math import exp, mean
import random


class ExchangeAgent:
    """
    ExchangeAgent implements automatic orders handling within the order book
    """
    id = 0

    def __init__(self, price: float or int = 100, std: float or int = 25, volume: int = 1000, rf: float = 5e-4,
                 transaction_cost: float = 0):
        """
        Creates ExchangeAgent with initialised order book and future dividends

        :param price: stock initial price
        :param std: standard deviation of order prices
        :param volume: number of orders initialised
        :param rf: risk-free rate
        :param transaction_cost: transaction cost on operations for traders
        """
        self.id = ExchangeAgent.id
        self.name = f'ExchangeAgent{self.id}'
        ExchangeAgent.id += 1
        self.volume = volume
        self.order_book = {'bid': OrderList('bid'), 'ask': OrderList('ask')}
        self.dividend_book = list()  # act like queue
        self.risk_free = rf
        self.transaction_cost = transaction_cost
        self._fill_book(price, std, volume, rf * price)  # initialise both order book and dividend book
        # logging.Logger.info(f"{self.name}")

    def generate_dividend(self):
        """
        Add new dividend to queue and pop last
        """
        # Generate future dividend
        d = self.dividend_book[-1] * self._next_dividend()
        self.dividend_book.append(max(d, 0))  # dividend > 0
        self.dividend_book.pop(0)

    def _fill_book(self, price, std, volume, div: float = 0.05):
        """
        Fill order book with random orders and fill dividend book with future dividends.

        **Order book:** generate prices from normal distribution with *std*, and *price* as center; generate
        quantities for these orders from uniform distribution with 1, 5 bounds. Set bid orders when
        order price is less than *price*, set ask orders when order price is greater than *price*.

        **Dividend book:** add 100 dividends using *_next_dividend* method.
        """
        # Order book
        prices1 = [round(random.normalvariate(price - std, std), 1) for _ in range(volume // 2)]
        prices2 = [round(random.normalvariate(price + std, std), 1) for _ in range(volume // 2)]
        quantities = [random.randint(1, 5) for _ in range(volume)]

        for (p, q) in zip(sorted(prices1 + prices2), quantities):
            if p > price:
                order = Order(round(p, 1), q, 'ask', self.id, None)
                self.order_book['ask'].append(order)
            else:
                order = Order(p, q, 'bid', self.id, None)
                self.order_book['bid'].push(order)

        # Dividend book
        for i in range(100):
            self.dividend_book.append(max(div, 0))  # dividend > 0
            div *= self._next_dividend()

    def _clear_book(self):
        """
        **(UNUSED)** Clear order book from orders with 0 quantity.
        """
        self.order_book['bid'] = OrderList.from_list([order for order in self.order_book['bid'] if order.qty > 0])
        self.order_book['ask'] = OrderList.from_list([order for order in self.order_book['ask'] if order.qty > 0])

    def spread(self) -> dict or None:
        """
        Returns best bid and ask prices as dictionary

        :return: {'bid': float, 'ask': float}
        """
        if self.order_book['bid'] and self.order_book['ask']:
            return {'bid': self.order_book['bid'].first.price, 'ask': self.order_book['ask'].first.price}
        raise Exception(f'There no either bid or ask orders')

    def spread_volume(self) -> dict or None:
        """
        **(UNUSED)** Returns best bid and ask volumes as dictionary

        :return: {'bid': float, 'ask': float}
        """
        if self.order_book['bid'] and self.order_book['ask']:
            return {'bid': self.order_book['bid'].first.qty, 'ask': self.order_book['ask'].first.qty}
        raise Exception(f'There no either bid or ask orders')

    def price(self) -> float:
        """
        Returns current stock price as mean between best bid and ask prices
        """

        spread = self.spread()
        if spread:
            return round((spread['bid'] + spread['ask']) / 2, 1)
        raise Exception(f'Price cannot be determined, since no orders either bid or ask')

    def dividend(self, access: int = None) -> list or float:
        """
        Returns either current dividend or *access* future dividends (if called by trader)

        :param access: the number of future dividends accessed by a trader
        """
        if access is None:
            return self.dividend_book[0]
        return self.dividend_book[:access]

    @classmethod
    def _next_dividend(cls, std=5e-3):
        return exp(random.normalvariate(0, std))

    def limit_order(self, order: Order):
        bid, ask = self.spread().values()
        t_cost = self.transaction_cost
        if not bid or not ask:
            return

        if order.order_type == 'bid':
            if order.price >= ask:
                order = self.order_book['ask'].fulfill(order, t_cost)
            if order.qty > 0:
                self.order_book['bid'].insert(order)
            return

        elif order.order_type == 'ask':
            if order.price <= bid:
                order = self.order_book['bid'].fulfill(order, t_cost)
            if order.qty > 0:
                self.order_book['ask'].insert(order)

    def market_order(self, order: Order) -> Order:
        t_cost = self.transaction_cost
        if order.order_type == 'bid':
            order = self.order_book['ask'].fulfill(order, t_cost)
        elif order.order_type == 'ask':
            order = self.order_book['bid'].fulfill(order, t_cost)
        return order

    def cancel_order(self, order: Order):
        if order.order_type == 'bid':
            self.order_book['bid'].remove(order)
        elif order.order_type == 'ask':
            self.order_book['ask'].remove(order)


class Trader:
    """
    Trader basic interface
    """
    id = 0

    def __init__(self, markets: List[ExchangeAgent], cash: float or int, assets: List[int]):
        """
        Trader that is activated on call to perform action

        :param markets: link to exchange agent
        :param cash: trader's cash available
        :param assets: trader's number of shares hold
        """
        self.type = 'Unknown'
        self.name = f'Trader{self.id}'
        self.id = Trader.id
        Trader.id += 1

        self.markets = markets
        self.orders = list()  # list of orders sitting in the order book

        self.cash = cash
        self.assets = assets
        # logging.Logger.info(f"{self.name} {len(assets)}")

    def __str__(self) -> str:
        return f'{self.name} ({self.type})'

    def equity(self) -> float:
        """
        Returns trader's value of cash and stock holdings
        """
        price = 0
        for _ in range(len(self.markets)):
            price += self.assets[_] * (self.markets[_].price() if self.markets[_].price() is not None else 0)
        return self.cash + price

    def _buy_limit(self, quantity, price, market_id):
        order = Order(round(price, 1), round(quantity), 'bid', market_id, self)
        self.orders.append(order)
        self.markets[market_id].limit_order(order)

    def _sell_limit(self, quantity, price, market_id):
        order = Order(round(price, 1), round(quantity), 'ask', market_id, self)
        self.orders.append(order)
        self.markets[market_id].limit_order(order)

    def _buy_market(self, quantity, market: Optional[int] = None) -> int:
        """
        :return: quantity unfulfilled
        """
        for _ in range(len(self.markets)):
            if self.markets[_].order_book['ask']:
                break
        else:
            return quantity
        mn_index = 0
        for _ in range(len(self.markets)):
            if self.markets[_].order_book['ask'].last and self.markets[mn_index].order_book['ask'] and \
                    self.markets[_].order_book['ask'].last.price < self.markets[mn_index].order_book['ask'].last.price:
                mn_index = _
        if market is not None:
            mn_index = market
        # logging.Logger.info(f"{self.name} ({self.type}) BUY {mn_index}/{len(self.markets)}")
        order = Order(self.markets[mn_index].order_book['ask'].last.price, round(quantity), 'bid', mn_index, self)
        return self.markets[mn_index].market_order(order).qty

    def _sell_market(self, quantity, market: int = None) -> int:
        """
        :return: quantity unfulfilled
        """
        for _ in range(len(self.markets)):
            if self.markets[_].order_book['bid']:
                break
        else:
            return quantity
        mx_index = 0
        for _ in range(len(self.markets)):
            if self.markets[_].order_book['bid'].last and self.markets[mx_index].order_book['bid'] and \
                    self.markets[_].order_book['bid'].last.price > self.markets[mx_index].order_book['bid'].last.price:
                mx_index = _
        if market is not None:
            mx_index = market
        # logging.Logger.info(f"{self.name} ({self.type}) SELL {mx_index}/{len(self.markets)}")
        order = Order(self.markets[mx_index].order_book['bid'].last.price, round(quantity), 'ask', mx_index, self)
        return self.markets[mx_index].market_order(order).qty

    def _cancel_order(self, order: Order):
        self.markets[order.market_id].cancel_order(order)
        self.orders.remove(order)


class Random(Trader):
    """
    Random creates noisy orders to recreate trading in real environment.
    """

    def __init__(self, markets: List[ExchangeAgent], cash: float or int, assets: List[int]):
        super().__init__(markets, cash, assets)
        self.type = 'Random'

    @staticmethod
    def draw_delta(std: float or int = 2.5):
        lamb = 1 / std
        return random.expovariate(lamb)

    @staticmethod
    def draw_price(order_type, spread: dict, std: float or int = 2.5) -> float:
        """
        Draw price for limit order. The price is calculated as:

        - 0.35 probability: within the spread - uniform distribution
        - 0.65 probability: out of the spread - delta from best price is exponential distribution r.v.
        :return: order price
        """
        random_state = random.random()  # Determines IN spread OR OUT of spread

        # Within the spread
        if random_state < .35:
            return random.uniform(spread['bid'], spread['ask'])

        # Out of spread
        else:
            delta = Random.draw_delta(std)
            if order_type == 'bid':
                return spread['bid'] - delta
            if order_type == 'ask':
                return spread['ask'] + delta

    @staticmethod
    def draw_quantity(a=1, b=5) -> float:
        """
        Draw order quantity for limit or market order. The quantity is drawn from U[a,b]

        :param a: minimal quantity
        :param b: maximal quantity
        :return: order quantity
        """
        return random.randint(a, b)

    def call(self):
        spread = list(filter(lambda x: x is not None, [self.markets[_].spread() for _ in range(len(self.markets))]))
        if len(spread) == 0:
            return
        spread = min(spread)
        random_state = random.random()

        if random_state > .5:
            order_type = 'bid'
        else:
            order_type = 'ask'

        random_state = random.random()
        # Market order
        if random_state > .85:
            quantity = self.draw_quantity()
            if order_type == 'bid':
                self._buy_market(quantity)
            elif order_type == 'ask':
                self._sell_market(quantity)

        # Limit order
        elif random_state > .5:
            price = self.draw_price(order_type, spread)
            quantity = self.draw_quantity()
            if order_type == 'bid':
                self._buy_limit(quantity, price, 0)
            elif order_type == 'ask':
                self._sell_limit(quantity, price, 0)

        # Cancellation order
        elif random_state < .35:
            if self.orders:
                order_n = random.randint(0, len(self.orders) - 1)
                self._cancel_order(self.orders[order_n])


class Fundamentalist(Trader):
    """
    Fundamentalist evaluate stock value using Constant Dividend Model. Then places orders accordingly
    """

    def __init__(self, markets: List[ExchangeAgent], cash: float or int, assets: List[int], access: int = 1):
        """
        :param markets: exchange agent link
        :param cash: number of cash
        :param assets: number of assets
        :param access: number of future dividends informed
        """
        super().__init__(markets, cash, assets)
        self.type = 'Fundamentalist'
        self.access = access

    @staticmethod
    def evaluate(dividends: list, risk_free: float):
        """
        Evaluates the stock using Constant Dividend Model.

        We first sum all known (based on *access*) discounted dividends. Then calculate perpetual value
        of the stock based on last known dividend.
        """
        divs = dividends  # known future dividends
        r = risk_free  # risk-free rate

        perp = divs[-1] / r / (1 + r) ** (len(divs) - 1)  # perpetual value
        known = sum([divs[i] / (1 + r) ** (i + 1) for i in range(len(divs) - 1)]) if len(divs) > 1 else 0  # known value
        return known + perp

    @staticmethod
    def draw_quantity(pf, p, gamma: float = 5e-3):
        """
        Draw order quantity for limit or market order. The quantity depends on difference between fundamental
        value and market price.

        :param pf: fundamental value
        :param p: market price
        :param gamma: dependency coefficient
        :return: order quantity
        """
        q = round(abs(pf - p) / p / gamma)
        return min(q, 5)

    def call(self):
        pf = round(self.evaluate(self.markets[0].dividend(self.access), self.markets[0].risk_free),
                   1)  # fundamental price
        p = self.markets[0].price()
        spread = self.markets[0].spread()
        t_cost = self.markets[0].transaction_cost

        if spread is None:
            return

        random_state = random.random()
        qty = Fundamentalist.draw_quantity(pf, p)  # quantity to buy
        if not qty:
            return

        # Limit or Market order
        if random_state > .45:
            random_state = random.random()

            ask_t = round(spread['ask'] * (1 + t_cost), 1)
            bid_t = round(spread['bid'] * (1 - t_cost), 1)

            if pf >= ask_t:
                if random_state > .5:
                    self._buy_market(qty)
                else:
                    self._sell_limit(qty, (pf + Random.draw_delta()) * (1 + t_cost), 0)

            elif pf <= bid_t:
                if random_state > .5:
                    self._sell_market(qty)
                else:
                    self._buy_limit(qty, (pf - Random.draw_delta()) * (1 - t_cost), 0)

            elif ask_t > pf > bid_t:
                if random_state > .5:
                    self._buy_limit(qty, (pf - Random.draw_delta()) * (1 - t_cost), 0)
                else:
                    self._sell_limit(qty, (pf + Random.draw_delta()) * (1 + t_cost), 0)

        # Cancel order
        else:
            if self.orders:
                self._cancel_order(self.orders[0])


class Chartist(Trader):
    """
    Chartists are searching for trends in the price movements. Each trader has sentiment - opinion
    about future price movement (either increasing, or decreasing). Based on sentiment trader either
    buys stock or sells. Sentiment revaluation happens at the end of each iteration based on opinion
    propagation among other chartists, current price changes
    """

    def __init__(self, markets: List[ExchangeAgent], cash: float or int, assets: List[int]):
        """
        :param markets: exchange agent link
        :param cash: number of cash
        :param assets: number of assets
        """
        super().__init__(markets, cash, assets)
        self.type = 'Chartist'
        self.sentiment = 'Optimistic' if random.random() > .5 else 'Pessimistic'

    def call(self):
        random_state = random.random()

        if self.sentiment == 'Optimistic':
            mn_index = 0
            for _ in range(len(self.markets)):
                if self.markets[_].price() < self.markets[mn_index].price():
                    mn_index = _
            t_cost = self.markets[mn_index].transaction_cost
            spread = self.markets[mn_index].spread()
            # Market order
            if random_state > .85:
                self._buy_market(Random.draw_quantity())
            # Limit order
            elif random_state > .5:
                self._buy_limit(Random.draw_quantity(), Random.draw_price('bid', spread) * (1 - t_cost), mn_index)
            # Cancel order
            elif random_state < .35:
                if self.orders:
                    self._cancel_order(self.orders[-1])
        elif self.sentiment == 'Pessimistic':
            mx_index = 0
            for _ in range(len(self.markets)):
                if self.markets[_].price() > self.markets[mx_index].price():
                    mx_index = _
            t_cost = self.markets[mx_index].transaction_cost
            spread = self.markets[mx_index].spread()
            # Market order
            if random_state > .85:
                self._sell_market(Random.draw_quantity())
            # Limit order
            elif random_state > .5:
                self._sell_limit(Random.draw_quantity(), Random.draw_price('ask', spread) * (1 + t_cost), mx_index)
            # Cancel order
            elif random_state < .35:
                if self.orders:
                    self._cancel_order(self.orders[-1])

    def change_sentiment(self, info, a1=1, a2=1, v1=.1):
        """
        Revaluate chartist's opinion about future price movement

        :param info: SimulatorInfo
        :param a1: importance of chartists opinion
        :param a2: importance of current price changes
        :param v1: frequency of revaluation of opinion for sentiment
        """
        n_traders = len(info.traders)  # number of all traders
        n_chartists = sum([tr_type == 'Chartist' for tr_type in info.types[-1].values()])
        n_optimistic = sum([tr_type == 'Optimistic' for tr_type in info.sentiments[-1].values()])
        n_pessimists = sum([tr_type == 'Pessimistic' for tr_type in info.sentiments[-1].values()])

        dp = info.prices[-1] - info.prices[-2] if len(info.prices) > 1 else 0  # price derivative
        if self.sentiment == 'Optimistic':
            p = min([self.markets[_].price() for _ in range(len(self.markets))])  # market price
            x = (n_optimistic - n_pessimists) / n_chartists

            if v1 == 0:
                v1 = 1
            if p == 0:
                p = 1
            U = a1 * x + a2 / v1 * dp / p
            prob = v1 * n_chartists / n_traders * exp(U)
            if prob > random.random():
                self.sentiment = 'Pessimistic'

        elif self.sentiment == 'Pessimistic':
            p = max([self.markets[_].price() for _ in range(len(self.markets))])  # market price
            x = (n_optimistic - n_pessimists) / n_chartists
            if v1 == 0:
                v1 = 1
            if p == 0:
                p = 1
            U = a1 * x + a2 / v1 * dp / p
            prob = v1 * n_chartists / n_traders * exp(-U)
            if prob > random.random():
                self.sentiment = 'Optimistic'


class Universalist(Fundamentalist, Chartist):
    """
    Universalist mixes Fundamentalist, Chartist trading strategies allowing to change one strategy to another
    """

    def __init__(self, markets: List[ExchangeAgent], cash: float or int, assets: List[int], access: int = 1):
        """
        :param markets: exchange agent link
        :param cash: number of cash
        :param assets: number of assets
        :param access: number of future dividends informed
        """
        super().__init__(markets, cash, assets)
        self.type = 'Chartist' if random.random() > .5 else 'Fundamentalist'  # randomly decide type
        self.sentiment = 'Optimistic' if random.random() > .5 else 'Pessimistic'  # sentiment about trend (Chartist)
        self.access = access  # next n dividend payments known (Fundamentalist)

    def call(self):
        """
        Call one of parents' methods depending on what type it is currently set.
        """
        if self.type == 'Chartist':
            Chartist.call(self)
        elif self.type == 'Fundamentalist':
            Fundamentalist.call(self)

    def change_strategy(self, info, a1=1, a2=1, a3=1, v1=.1, v2=.1, s=.1):
        """
        Change strategy or sentiment

        :param info: SimulatorInfo
        :param a1: importance of chartists opinion
        :param a2: importance of current price changes
        :param a3: importance of fundamentalist profit
        :param v1: frequency of revaluation of opinion for sentiment
        :param v2: frequency of revaluation of opinion for strategy
        :param s: importance of fundamental value opportunities
        """
        # Gather variables
        n_traders = len(info.traders)  # number of all traders
        n_fundamentalists = sum([tr.type == 'Fundamentalist' for tr in info.traders.values()])
        n_optimistic = sum([tr.sentiment == 'Optimistic' for tr in info.traders.values() if tr.type == 'Chartist'])
        n_pessimists = sum([tr.sentiment == 'Pessimistic' for tr in info.traders.values() if tr.type == 'Chartist'])

        dp = info.prices[-1] - info.prices[-2] if len(info.prices) > 1 else 0  # price derivative
        p = self.markets[0].price()  # market price
        pf = self.evaluate(self.markets[0].dividend(self.access), self.markets[0].risk_free)  # fundamental price
        r = pf * self.markets[0].risk_free  # expected dividend return
        R = mean(info.returns[-1].values())  # average return in economy

        # Change sentiment
        if self.type == 'Chartist':
            Chartist.change_sentiment(self, info, a1, a2, v1)

        # Change strategy
        U1 = max(-100, min(100, a3 * ((r + 1 / v2 * dp) / p - R - s * abs((pf - p) / p))))
        U2 = max(-100, min(100, a3 * (R - (r + 1 / v2 * dp) / p - s * abs((pf - p) / p))))

        if self.type == 'Chartist':
            if self.sentiment == 'Optimistic':
                prob = v2 * n_optimistic / (n_traders * exp(U1))
                if prob > random.random():
                    self.type = 'Fundamentalist'
            elif self.sentiment == 'Pessimistic':
                prob = v2 * n_pessimists / (n_traders * exp(U2))
                if prob > random.random():
                    self.type = 'Fundamentalist'

        elif self.type == 'Fundamentalist':
            prob = v2 * n_fundamentalists / (n_traders * exp(-U1))
            if prob > random.random() and self.sentiment == 'Pessimistic':
                self.type = 'Chartist'
                self.sentiment = 'Optimistic'

            prob = v2 * n_fundamentalists / (n_traders * exp(-U2))
            if prob > random.random() and self.sentiment == 'Optimistic':
                self.type = 'Chartist'
                self.sentiment = 'Pessimistic'


class MarketMaker(Trader):
    """
    MarketMaker creates limit orders on both sides of the spread trying to gain on
    spread between bid and ask prices, and maintain its assets to cash ratio in balance.
    """

    def __init__(self, markets: List[ExchangeAgent], cash: float, assets: List[int], softlimits: List[int] = None):
        super().__init__(markets, cash, assets)
        if softlimits is None:
            softlimits = [100] * len(self.markets)
        self.softlimits = softlimits
        self.type = 'Market Maker'
        self.uls = self.softlimits
        self.lls = [-softlimit for softlimit in self.softlimits]
        self.panic = False
        self.prev_cash = cash

    def call(self):
        for order in self.orders.copy():
            self._cancel_order(order)
        for i in range(len(self.markets)):
            spread = self.markets[i].spread()
            base_offset = min(1, (spread['ask'] - spread['bid']) * (self.assets[i] / self.lls[i]))
            bid_volume = max(0, (self.uls[i] - 1 - self.assets[i]) // 2)
            ask_volume = max(0, (self.assets[i] - 1 - self.lls[i]) // 2)
            bid_price = spread['bid'] + base_offset
            ask_price = spread['ask'] - base_offset
            self.panic = True
            self._buy_limit(bid_volume, bid_price, i)
            self._sell_limit(ask_volume, ask_price, i)
        self.prev_cash = self.cash
