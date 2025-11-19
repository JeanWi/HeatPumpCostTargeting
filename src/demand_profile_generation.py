import math

import pandas as pd


def generate_batch_process(hour_on:float, hour_off:float, length_on:float, length_off:float) -> list:
    """
    Generates a batch process for a full year with every day having the same profile

    :param float hour_on: Starting hour of the day (before, demand is 0)
    :param float hour_off: Ending hour of the day (after, demand is 0)
    :param float length_on: length of process in hours
    :param float length_off: pause between process in hours
    :return: annual quarter-hourly demand profile
    """
    available_time_per_day = hour_off - hour_on
    batches_per_day = available_time_per_day/(length_off+length_on)

    profile_one_batch = [1] * int(length_on * 4) + [0] * int(length_off * 4)
    profile_n_batches = profile_one_batch * math.floor(batches_per_day)
    profile_day_beginning = [0] * int(hour_on * 4) + profile_n_batches
    hours_missing = 24*4 - len(profile_day_beginning)
    profile_day = profile_day_beginning + [0]*int(hours_missing)
    profile_year = profile_day * 365
    return profile_year


def generate_continuous_process(hourly_demand: list) -> list:
    """
    Generate a continuous quarter-hourly demand profile from hourly demand profile

    :param list hourly_demand: list of length 24 with hourly demand values
    :return: annual quarter-hourly demand profile
    """
    profile_day = [x for x in hourly_demand for _ in range(4)]
    profile_year = profile_day * 365
    return profile_year


def generate_demand_profile_template(weekend_different: bool, weekend_scale: float) -> pd.DataFrame:
    date_rng = pd.date_range(start='2025-01-01', end='2025-12-31 23:45:00', freq='15min')
    df = pd.DataFrame(date_rng, columns=['datetime'])
    df['demand'] = 0
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['scaled_process'] = 1
    if weekend_different:
        df['scaled_process'] = df['day_of_week'].isin([5, 6]).apply(lambda x: weekend_scale / 100 if x else 1)

    return df
