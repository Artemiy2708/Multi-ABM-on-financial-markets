from __future__ import annotations

import random
from typing import List

from AgentBasedModel.simulator import Simulator
from AgentBasedModel.agents import Trader, Universalist, Fundamentalist, MarketMaker
from AgentBasedModel.utils.orders import Order
from itertools import chain

colors = [
    (31, 119, 180),  # blue
    (255, 127, 14),  # orange
    (44, 160, 44),  # green
    (214, 39, 40),  # red
    (148, 103, 189),  # purple
    (140, 86, 75),  # brown
    (227, 119, 194),  # pink
    (127, 127, 127),  # gray
    (188, 189, 34),  # yellow-green
    (23, 190, 207),  # cyan
]

colors = [(r / 255.0, g / 255.0, b / 255.0) for r, g, b in colors]


class Event:
    def __init__(self, it: int):
        self.color = colors[0]
        self.it = it  # Activation it
        self.simulator: Simulator | None = None
        self.stock_id = None

    def __repr__(self):
        return f'empty (it={self.it})'

    def call(self, it: int):
        if self.simulator is None:
            raise Exception('No simulator link found')
        if it != self.it:
            return True
        return False

    def link(self, simulator: Simulator):
        self.simulator = simulator
        if self.stock_id is None:
            self.stock_id = random.randint(0, len(self.simulator.exchanges) - 1)
        return self

    def to_dict(self) -> dict:
        return {
            'it': self.it,
            'type': self.__class__.__name__,
        }


class FundamentalPriceShock(Event):
    def __init__(self, it: int, price_change: float, stock_id: int = None):
        super().__init__(it)
        self.color = colors[1]
        self.dp = price_change
        self.stock_id = stock_id

    def __repr__(self):
        return f'fundamental price shock (it={self.it}, dp={self.dp})'

    def call(self, it: int):
        if super().call(it):
            return

        divs = self.simulator.exchanges[self.stock_id].dividend_book  # link to dividend book
        r = self.simulator.exchanges[self.stock_id].risk_free  # risk-free rate

        self.simulator.exchanges[self.stock_id].dividend_book = [div + self.dp * r for div in divs]


class MarketPriceShock(Event):
    def __init__(self, it: int, price_change: float, stock_id: int = None):
        super().__init__(it)
        self.color = colors[2]
        self.dp = round(price_change)
        self.stock_id = stock_id

    def __repr__(self):
        return f'market price shock (it={self.it}, dp={self.dp})'

    def call(self, it: int):
        if super().call(it):
            return
        book = self.simulator.exchanges[self.stock_id].order_book
        for order in chain(*book.values()):
                order.price += round(self.dp, 1)



class LiquidityShock(Event):
    def __init__(self, it: int, volume_change: float, stock_id: int = None):
        super().__init__(it)
        self.color = colors[3]
        self.dv = round(volume_change)
        self.stock_id = stock_id

    def __repr__(self):
        return f'liquidity shock (it={self.it}, dv={self.dv})'

    def call(self, it: int):
        if super().call(it):
            return
        exchanges = self.simulator.exchanges
        pseudo_trader = Trader(exchanges, 1e6, [int(1e4)])
        if self.dv < 0:
            order = Order(exchanges[self.stock_id].order_book['ask'].last.price, abs(self.dv), 'bid', 0, pseudo_trader)
        else:  # sell
            order = Order(exchanges[self.stock_id].order_book['bid'].last.price, abs(self.dv), 'ask', 0, pseudo_trader)
        exchanges[self.stock_id].market_order(order)


class InformationShock(Event):
    def __init__(self, it, access: int, stock_id: int = None):
        super().__init__(it)
        self.color = colors[4]
        self.access = access
        self.stock_id = stock_id

    def __repr__(self):
        return f'information shock (it={self.it}, access={self.access})'

    def call(self, it: int):
        if super().call(it):
            return
        for trader in self.simulator.traders:
            if type(trader) in (Universalist, Fundamentalist):
                trader.access = self.access


class MarketMakerIn(Event):
    def __init__(self, it, cash: float = 10 ** 3, assets: List[int] = None, softlimits: List[int] = None,
                 stock_id: int = None):
        super().__init__(it)
        self.color = colors[5]
        if assets is None:
            assets = [0]
        if softlimits is None:
            softlimits = [100]
        self.cash = cash
        self.assets = assets
        self.softlimits = softlimits
        self.stock_id = stock_id

    def __repr__(self):
        return f'mm in (it={self.it}, softlimits={self.softlimits})'

    def call(self, it: int):
        if super().call(it):
            return

        maker = MarketMaker(self.simulator.exchanges, self.cash, self.assets, self.softlimits)
        self.simulator.traders.append(maker)


class MarketMakerOut(Event):
    def __init__(self, it, stock_id: int = None):
        super().__init__(it)
        self.color = colors[6]
        self.stock_id = stock_id

    def __repr__(self):
        return f'mm out (it={self.it})'

    def call(self, it: int):
        if super().call(it):
            return

        self.simulator.traders = [tr for tr in self.simulator.traders if type(tr) != MarketMaker]


class TransactionCost(Event):
    def __init__(self, it, cost, stock_id: int = None):
        super().__init__(it)
        self.color = colors[7]
        self.cost = cost
        self.stock_id = stock_id

    def __repr__(self):
        return f'transaction cost (it={self.it}, cost={self.cost}%)'

    def call(self, it: int):
        if super().call(it):
            return
        self.simulator.exchanges[self.stock_id].transaction_cost = self.cost

class StopTrading(Event):
    def __init__(self, it: int, price_change_zero: float, stock_id: int = None):
        super().__init__(it)
        self.color = colors[8]
        self.dp = round(price_change_zero)
        self.stock_id = stock_id

    def __repr__(self):
        return f'stop exchange price shock (it={self.it}, dp={self.dp})'

    def call(self, it: int):
        if super().call(it):
            return
        book = self.simulator.exchanges[self.stock_id].order_book
        for order in chain(*book.values()):
            for i in range(10000):
                order.price += round(self.dp, 1)

