import json
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

from AgentBasedModel.utils import math, Logger


def make_df(json_path: str = "info_0.json", info: Optional[Dict] = None, config: Dict = None) -> pd.DataFrame:
    if not info:
        with open(json_path, "r", encoding="utf-8") as f:
            info = json.loads(f.read())
    df = pd.DataFrame(
        columns=['Iteration', 'Price', 'AvgReturn', 'Dividends', 'Random', 'MarketMaker', 'Chartist', 'Fundamentalist',
                 'Traders', 'State'])
    info['states'] = [state for state in info['states'] for _
                      in range(config['window'])]
    info['states'] += ['stable'] * (len(info['prices']) - len(info['states']))
    for i in range(len(info['prices'])):
        avg_return = sum([value for key, value in info['returns'][i].items()]) / len(info['returns'][i].keys())
        traders = info['orders'][i]['traders']
        random_count = len(list(filter(lambda x: "Random" in x, traders)))
        market_maker_count = len(list(filter(lambda x: "Market Maker" in x, traders)))
        chartist_count = len(list(filter(lambda x: "Chartist" in x, traders)))
        fundamentalist_count = len(list(filter(lambda x: "Fundamentalist" in x, traders)))
        traders_count = len(traders)
        df.loc[i] = [
            i + 1,
            info['prices'][i],
            info['dividends'][i],
            avg_return,
            random_count,
            market_maker_count,
            chartist_count,
            fundamentalist_count,
            traders_count,
            info['states'][i],
        ]
    return df


def make_event_df(info: Any = None, config: Dict = None):
    info_dict = info.to_dict(config)
    data = list()
    # data =
    events = config['events']
    # events = list(filter(lambda item: item['stock_id'] == stock_id, events))
    events = sorted(events, key=lambda item: item['it'])
    available_traders = [value['name'] for key, value in info_dict['available_traders'].items()]
    traders = dict()
    traders["random"] = len(list(filter(lambda x: "Random" in x, available_traders)))
    traders["market_maker"] = len(list(filter(lambda x: "MarketMaker" in x, available_traders)))
    traders["chartist"] = len(list(filter(lambda x: "Chartist" in x, available_traders)))
    traders["fundamentalist"] = len(list(filter(lambda x: "Fundamentalist" in x, available_traders)))
    for event in events:
        state_it = event['it'] // config['size'] - 1
        Logger.info(state_it)
        Logger.info(event['it'])
        is_recovered = False
        c = 0
        C = 0  # number of iterations until recover (right side)
        for s in info_dict['states'][state_it:]:
            if is_recovered:
                break

            C += 1
            c += 1
            if s in ('panic', 'disaster'):
                c = 0

            if c >= config['stability_threshold']:
                is_recovered = True

        if not is_recovered:
            time_to_recover = np.nan
        elif C == c:
            time_to_recover = 0
        else:
            shock_st_right = (state_it + 1) * config['size'] + config['window']  # right bound of interval of shock
            time_to_recover = (shock_st_right - event['it']) + C * config['size']  # right side of last window
            Logger.info(shock_st_right)
            Logger.info(time_to_recover)
        # Price, Return metrics
        prices = info_dict['prices'][1:]
        returns = info.stock_returns(1)

        l, r = max(event['it'] - 1 - 10, 0), event['it'] - 1  # -1 because we shift prices and returns to right
        before_price = math.mean(prices[l:r])
        l, r = max(event['it'] - 1 - 50, 0), event['it'] - 1  # -1 because we shift prices and returns to right
        before_return = math.mean(returns[l:r])

        after_price = np.nan
        after_return = np.nan

        if is_recovered:
            it_recovered = event['it'] - 1 + time_to_recover
            l, r = it_recovered, min(it_recovered + 10, config['iterations'] - 2)
            after_price = math.mean(prices[l:r]) if l < r else prices[r]
            l, r = it_recovered, min(it_recovered + 50, config['iterations'] - 2)
            after_return = math.mean(returns[l:r + config['size']]) if l < r else prices[r]
        data.append({
            # "type": event['type'],
            **event,
            "stock_id": info.exchange.id,
            **traders,
            'is_recovered': is_recovered,
            'time_to_recover': time_to_recover,
            'before_price': before_price,
            'after_price': after_price,
            'before_return': before_return,
            'after_return': after_return
        })
    return pd.DataFrame(data)
