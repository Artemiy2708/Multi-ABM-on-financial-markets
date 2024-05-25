import pandas as pd

import numpy as np
import tqdm

import AgentBasedModel

import json

from AgentBasedModel import plot_price_fundamental, plot_arbitrage, plot_price, plot_dividend, plot_orders, utils,StopTrading

with open("config_random_only_stop_exchange.json", "r", encoding="utf-8") as f:
    config = json.loads(f.read())
AgentBasedModel.ExchangeAgent.id = 0
AgentBasedModel.Trader.id = 0
exchanges = []
traders = []
events = []
chartists_present = []
for simulation in range(100):
    for exchange in config["exchanges"]:
        exchanges.append(AgentBasedModel.ExchangeAgent(**exchange))
    for trader in config["traders"]:
        params = dict(**trader)
        params.pop("type")
        params.pop("count")
        params["markets"] = [exchanges[_] for _ in trader["markets"]]
        traders.extend(
            [
                getattr(AgentBasedModel.agents, trader["type"])(**params) for _ in range(trader["count"])
            ]
        )
    for event in config["events"]:

        params = dict(**event)
        params.pop("type")
        events.append(
                getattr(AgentBasedModel.events, event["type"])(**params)
            )
        simulator = AgentBasedModel.Simulator(**{
            'exchanges': exchanges,
            'traders': traders,
            'events': events,
        })
        simulator.simulate(config["iterations"])
        infos = simulator.info
    for _ in range(len(infos)):
        info_dict = infos[_].to_dict(config)
        plot_price_fundamental(infos[_])
        plot_arbitrage(infos[_])
        plot_price(infos[_])
        plot_dividend(infos[_])
        plot_orders(infos[_])
        df = AgentBasedModel.utils.make_df(info=info_dict, config=config)
    chartists_present.append(df['Price'][50::])
final_df = pd.concat(chartists_present)
final_df.to_csv('random_only_stop_exchange.csv')
