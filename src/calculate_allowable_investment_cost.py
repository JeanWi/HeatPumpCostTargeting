import pandas as pd
import streamlit as st

from src.carnot_hp_calculations import calculate_cop, calculate_annuity_factor

def calculate_allowable_investment_cost(
        heat_demand: pd.Series,
        p_el: pd.Series,
        p_alt: float,
        T_l: float,
        T_h: float,
        exergetic_efficiency: float,
        interest_rate: float,
        lifetime: int
):
    cop = calculate_cop(T_l + 273, T_h + 273, exergetic_efficiency)

    # st.write(T_l)
    # st.write(T_h)
    # st.write(exergetic_efficiency)
    # st.write(cop)

    delta_t = heat_demand.index.diff().dropna()[0].total_seconds() / 3600

    # cost alternative
    heat_consumption = heat_demand * delta_t
    total_heat_demand = heat_consumption.sum()
    total_cost_alternative = total_heat_demand * p_alt

    # cost hp
    electricity_power = heat_demand / cop
    electricity_consumption = electricity_power * delta_t
    electricity_costs = electricity_consumption*p_el
    total_cost_hp = electricity_costs.sum()
    electric_capacity_hp = 1 / cop

    f = calculate_annuity_factor(interest_rate, lifetime)

    allowable_costs = (total_cost_alternative - total_cost_hp) / electric_capacity_hp * f

    return allowable_costs







