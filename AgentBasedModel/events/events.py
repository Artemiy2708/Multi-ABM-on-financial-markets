class StopTrading(Event):
    def __init__(self, it: int, exchange_id: int):
        super().__init__(it)
        self.color = colors[8]  # Define a new color for this event
        self.exchange_id = exchange_id

    def __repr__(self):
        return f'stop trading (it={self.it}, exchange={self.exchange_id})'

    def call(self, it: int):
        if super().call(it):
            return

        for i, exchange in enumerate(self.simulator.exchanges):
            if i == self.exchange_id:
                exchange.trading_stopped = True
            else:
                exchange.trading_stopped = False

    def to_dict(self) -> dict:
        event_dict = super().to_dict()
        event_dict['exchange_id'] = self.exchange_id
        return event_dict
