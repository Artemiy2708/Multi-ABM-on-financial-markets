import itertools
from typing import List, Dict


class ConfigGenerator:
    def __init__(self, **kwargs):
        self.scenarios = kwargs.get("scenarios", dict())
        self.result = {}

    def generate(self, **kwargs) -> Dict:
        for scenario, config in self.scenarios.items():
            self.result[scenario] = self.generate_scenario(**kwargs, **config)
        return self.result

    def generate_scenario(self, **kwargs) -> list:
        events = kwargs.get("events", list())
        market_makers = kwargs.get("market_makers", list())
        chartists = kwargs.get("chartists", list())
        randoms = kwargs.get("randoms", list())
        fundamentalists = kwargs.get("fundamentalists", list())
        size = kwargs.get("size", 10)
        stability_threshold = kwargs.get("stability_threshold", 5)
        iterations = kwargs.get("iterations", 1)
        window = kwargs.get("window", 5)
        configs = list()
        for events in itertools.product(*[*events]):
            for traders in itertools.product(*[*market_makers, *chartists, *randoms, *fundamentalists]):
                configs.append(
                    {
                        "exchanges": [
                            {
                                "volume": 3000
                            },
                            {
                                "volume": 3000
                            }
                        ],
                        "events": list(events),
                        "traders": list(traders),
                        "size": size,
                        "window": window,
                        "stability_threshold": stability_threshold,
                        "iterations": iterations,
                    }
                )
        return configs


def generate_configs(**kwargs) -> Dict:
    base_event = {
        "type": "MarketPriceShock",
        "it": 200,
        "price_change": -50,
        "stock_id": 0
    }
    base_market_maker = {
        "count": 10,
        "type": "MarketMaker",
        "cash": 10000,
        "markets": [
            0,
            1
        ],
        "softlimits": [
            100,
            100
        ],
        "assets": [
            0,
            0
        ]
    }
    base_chartist = {
        "count": 10,
        "type": "Chartist",
        "cash": 1000,
        "markets": [
            0,
            1
        ],
        "assets": [
            0,
            0
        ]
    }
    base_random = {
        "count": 10,
        "type": "Random",
        "markets": [
            1
        ],
        "cash": 1000,
        "assets": [
            0
        ]
    }
    base_fundamentalist = {
        "count": 10,
        "type": "Fundamentalist",
        "markets": [0],
        "cash": 1000,
        "assets": [0]
    }
    scenarios = {
        "scenario1": {
            "events": [
                [{
                    **base_event,
                    "price_change": price_change,
                } for price_change in [-50, -25, -5, 5, 25, 50]],
            ],
            "market_makers": [
                [{
                    **base_market_maker,
                    "count": count,
                } for count in [1, 5, 10, 25, 100]]
                # } for count in [5]]
            ],
            "chartists": [
                [{
                    **base_chartist,
                    "count": count,
                } for count in [5, 10, 25]]
                # } for count in [5]]
            ],
            "randoms": [
                [{
                    **base_random,
                    "count": count,
                } for count in [20, 50]]
                # } for count in [20]]
            ],
            "fundamentalists": [
                [{
                    **base_fundamentalist,
                    "count": count,
                } for count in [10, 25]]
                # } for count in [10]]
            ],
        },
    }
    generator = ConfigGenerator(scenarios=scenarios)
    return generator.generate(**kwargs)
