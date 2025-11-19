import numpy as np
import pandas as pd
import streamlit as st
from statsmodels import api as sm

def unlog_prices(p: pd.Series) -> pd.Series:
    return pd.Series(np.exp(p))

def fit_trends(X, y) -> dict:
    trend_params = {}
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    trend_params["X_0"] = model.params["const"]
    trend_params["gamma"] = model.params["int_time_step"]
    return trend_params

def determine_year_shift(p: pd.DataFrame) -> float:
    idxmin = p.groupby(["weekday", "hour"]).mean()["log(p) no trend"].idxmin()
    weekday, hour = idxmin

    year_shift = p[(p["weekday"] == weekday) & (p["hour"] == hour)]["int_time_step"][0]
    rho = (year_shift) * np.pi / 168
    return rho

def fit_week_cycle(X, y, rho) -> dict:
    weekly_trend = {}
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    weekly_trend["alpha"] = model.params["const"]
    weekly_trend["beta"] = model.params["int_time_step"]
    return weekly_trend


def add_time_columns(p: pd.DataFrame, selected_year=None) -> pd.DataFrame:
    p["year"] = p.index.year
    p["month"] = p.index.month
    p["weekday"] = p.index.weekday
    p["day"] = p.index.day
    p["hour"] = p.index.hour
    if selected_year is not None:
        p = p[p["year"] == selected_year]

    p["int_time_step"] = range(len(p))

    winter_months = [12, 1, 2]
    spring_months = [3, 4, 5]
    summer_months = [6, 7, 8]
    autumn_months = [9, 10, 11]

    p["winter"] = p["month"].isin(winter_months)
    p["spring"] = p["month"].isin(spring_months)
    p["summer"] = p["month"].isin(summer_months)
    p["autumn"] = p["month"].isin(autumn_months)
    p["weekend"] = p["weekday"].isin([5, 6])
    return p

def fit_daily_cycle(p: pd.DataFrame) -> dict:
    hourly_means = p.groupby(["winter", "spring", "summer", "autumn", "weekend", "hour"]).mean()[
        "log(p) no weekly cycle"]

    hourly_means.name = "hourly_cycle_log"

    return hourly_means

@st.cache_data
def fit_electricty_price_trends(p: pd.DataFrame, selected_years) -> tuple:
    """
    Fits electricity price trends (drift over the year, annual, weekly, daily) based on
    https://www.sciencedirect.com/science/article/pii/S0140988311001721#f0015

    :param pd.DataFrame p: Dataframe with datetime index and column p
    :return: dictonary with fitting coefficients
    """
    params = {}

    # add time_cols
    p = add_time_columns(p, selected_years)

    # Remove negative prices
    p["p_non_neg"] = np.where(p["p"] <= 0, 0.01, p["p"])
    # Log electricity price
    p["log(p)"] = np.log(p["p_non_neg"])

    # Fit trend
    trend_params = fit_trends(p["int_time_step"], p["log(p)"])
    params["trend"] = trend_params

    p["trend"] = trend_params["X_0"] + trend_params["gamma"] * p["int_time_step"]
    p["log(p) no trend"] = p["log(p)"] - p["trend"]

    # Fit weekly cycle
    phase_shift = determine_year_shift(p)
    x = np.abs(np.sin(p["int_time_step"] * np.pi / 168 - phase_shift))
    y = p["log(p) no trend"]
    week_params = fit_week_cycle(x, y, phase_shift)
    params["weekly_cycle"] = week_params
    params["weekly_cycle"]["phase_shift"] = phase_shift

    p["weekly_cycle"] = week_params["alpha"] + week_params["beta"] * np.abs(
        np.sin(p["int_time_step"] * np.pi / 168 - phase_shift))
    p["log(p) no weekly cycle"] = p["log(p) no trend"] - p["weekly_cycle"]

    # Fit hourly cycle
    week_params = fit_daily_cycle(p)
    params["hourly_cycle"] = week_params

    p["hourly_mean"] = p.groupby(["winter", "spring", "summer", "autumn", "weekend", "hour"])[
        "log(p) no weekly cycle"].transform("mean")
    p["log(p) randomness"] = p["log(p) no weekly cycle"] - p["hourly_mean"]

    p["log(p)_cycle_only"] = p["hourly_mean"] + p["weekly_cycle"] + p["trend"]

    p["p_cycle_only"] = unlog_prices(p["log(p)_cycle_only"])

    return p, params

@st.cache_data
def generate_electricity_price_profile(params, p_mean, scaling_factors, year):
    date_rng = pd.date_range(start=str(year) + '-01-01', end=str(year) + '-12-31 23:45:00', freq='1h')
    p = pd.DataFrame(index=date_rng)
    p = add_time_columns(p)

    trend = (params["trend"]["X_0"] + params["trend"]["gamma"] * p["int_time_step"]* scaling_factors["trend"])

    weekly_cycle = (params["weekly_cycle"]["alpha"] + params["weekly_cycle"]["beta"] * np.abs(
        np.sin(p["int_time_step"] * np.pi / 168 -  params["weekly_cycle"]["phase_shift"])))*scaling_factors["weekly_factor"]

    hourly_cycle = pd.merge(p, params["hourly_cycle"],right_on=["winter", "spring", "summer", "autumn", "weekend", "hour"], left_on=["winter", "spring", "summer", "autumn", "weekend", "hour"])
    hourly_cycle = hourly_cycle["hourly_cycle_log"] * scaling_factors["hourly_factor"]

    price_profile = np.exp(trend.values + weekly_cycle.values + hourly_cycle.values)

    price_profile_zero_mean = (price_profile - price_profile.mean()) * scaling_factors["overall_factor"]

    p["p"] = price_profile_zero_mean + p_mean


    return p

@st.cache_data
def load_electricity_price_profile(ctr_sel):
    p = pd.read_csv(f"data/european_wholesale_electricity_price_data_hourly/{ctr_sel}.csv", header=[0])
    p.index =  pd.to_datetime(p["Datetime (Local)"])
    p = p[["Price (EUR/MWhe)"]]
    p.columns = ["p"]
    return p
