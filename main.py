import pandas as pd

import AgentBasedModel
import random
import json

from AgentBasedModel import plot_price_fundamental, plot_arbitrage, plot_price, plot_dividend, plot_orders, utils
from AgentBasedModel.utils import logging

with open("config.json", "r", encoding="utf-8") as f:
    config = json.loads(f.read())
logging.Logger.info(f"Config: {json.dumps(config)}")

configs = AgentBasedModel.utils.generate_configs(iterations=2000)
with open(f"output/scenarios.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(configs))
for scenario, scenario_configs in configs.items():
    AgentBasedModel.utils.logging.Logger.error(f"Scenario: {scenario}. Configs: [{len(scenario_configs)}]")
    events_dfs = []
    for config_i, config in enumerate(scenario_configs):
        AgentBasedModel.ExchangeAgent.id = 0
        AgentBasedModel.Trader.id = 0
        AgentBasedModel.utils.logging.Logger.error(f"Config: #{config_i}")
        exchanges = []
        traders = []
        events = []

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
            # info_dict = infos[_].to_dict(config)
            # with open(f"output/info/json/{config_i}_{_}.json", "w", encoding="utf-8") as f:
            #     f.write(json.dumps(info_dict))
            # df = AgentBasedModel.utils.export.make_df(info=info_dict, config=config)
            # df.to_csv(f"output/info/csv/{config_i}_{_}.csv", index=False)

            events_dfs.append(AgentBasedModel.utils.make_event_df(info=infos[_], config=config))

            plot_price_fundamental(infos[_], save_path=f"output/plots/{config_i}_price_fundamental_{_}.png")
            plot_arbitrage(infos[_], save_path=f"output/plots/{config_i}_arbitrage_{_}.png")
            plot_price(infos[_], save_path=f"output/plots/{config_i}_price_{_}.png")
            plot_dividend(infos[_], save_path=f"output/plots/{config_i}_dividend_{_}.png")
            plot_orders(infos[_], save_path=f"output/plots/{config_i}_orders_{_}.png")
    events_dfs = pd.concat(events_dfs)
    events_dfs.to_csv(f"output/scenarios/{scenario}.csv", index=False)
# config = configs[]
# simulator.simulate(config["iterations"])
#
# infos = simulator.info
#
# for _ in range(len(infos)):
#     info_dict = infos[_].to_dict(config)
#     with open(f"info_{_}.json", "w", encoding="utf-8") as f:
#         f.write(json.dumps(info_dict))
#     df = AgentBasedModel.utils.export.make_df(info=info_dict, config=config)
#     df.to_csv(f"info_{_}.csv", index=False)
#
#     events_df = AgentBasedModel.utils.make_event_df(info=infos[_], config=config)
#     events_df.to_csv(f"events_{_}.csv", index=False)
#
#     plot_price_fundamental(infos[_])
#     plot_arbitrage(infos[_])
#     plot_price(infos[_])
#     plot_dividend(infos[_])
#     plot_orders(infos[_])
