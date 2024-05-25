import pandas as pd
import numpy as np
import AgentBasedModel
import json
from AgentBasedModel import plot_price_fundamental, plot_arbitrage, plot_price, plot_dividend, plot_orders, utils

with open("config_market_price_shock.json", "r", encoding="utf-8") as f:
    config = json.loads(f.read())
AgentBasedModel.ExchangeAgent.id = 0
AgentBasedModel.Trader.id = 0
exchanges = []
traders = []
events = []
all_dfs = []
for simulation in range(1000):
    config['events'][0]['price_change'] = np.random.randint(-50, -10)
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
        if _ == 0:
            final_prices_stock_zero = df['Price'].to_list()[200::]
        else:
            final_prices_stock_one = df['Price'].to_list()[200::]
    df = pd.DataFrame(columns=['zero', 'one', 'shock_value'], index=range(1, 1801))
    df['shock_value'] = config['events'][0]['price_change']
    df['zero'] = final_prices_stock_zero
    df['one'] = final_prices_stock_one
    all_dfs.append(df)
final_df = pd.concat(all_dfs)
final_df.to_csv('market_shock.csv')
