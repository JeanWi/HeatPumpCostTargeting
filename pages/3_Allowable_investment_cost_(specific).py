import pandas as pd
import streamlit as st
from src import manage_cash
import altair as alt
import numpy as np
import os
from src.get_price_data import process_price_data

from src.carnot_hp_calculations import *

manage_cash()

if len(st.session_state['demand_profiles'].keys()) == 0:
    st.error("Please specify a demand profile first ")
    st.page_link("pages/4_Generate_process_heat_demand_profile.py", label="Do this here", icon="📈")
else:

    st.markdown("**Heat pump specs**")
    exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0, step=0.5) /100
    lifetime = st.number_input("Lifetime of heat pump", value=15, min_value = 0, max_value = 100)
    interest_rate = st.number_input("Interest rate", value=5.0, min_value = 0.1, max_value = 20.0) / 100

    st.markdown("**Alternative heat provision**")
    p_th = st.number_input("Cost of alternative heat provision (EUR/MWth)", value=50, min_value = 0, max_value = 2000)/1000

    st.markdown("**Electricity price**")
    profile_type = st.selectbox("Type", ["Constant electricity price", "Price profile (day ahead, excluding taxes and levies)"])


    if profile_type == "Constant electricity price":
        p_el = st.number_input("Cost of electricity for heat pump (EUR/MWel)", value=150, min_value = 0, max_value = 300)/1000
        p_el = [p_el] * 8760*4
    else:
        ctrs_available = [f.replace(".csv", "") for f in os.listdir("data/european_wholesale_electricity_price_data_hourly") if f.endswith(".csv")]
        ctr_sel = st.selectbox("Use price from country", ctrs_available)

        p_el_profiles = pd.read_csv(f"data/european_wholesale_electricity_price_data_hourly/{ctr_sel}.csv", header=[0])
        p_el_profiles.index =  pd.to_datetime(p_el_profiles["Datetime (Local)"])
        p_el_profiles = p_el_profiles["Price (EUR/MWhe)"]

        counts = p_el_profiles.groupby(p_el_profiles.index.year).size()
        full_years = counts[counts >= 8760].index
        p_el_profiles = p_el_profiles[p_el_profiles.index.year.isin(full_years)]

        yrs_available = full_years.tolist()
        year_sel = st.selectbox("Use price from year", yrs_available)
        p_el_profiles = p_el_profiles.loc[p_el_profiles.index.year == year_sel]

        industrial_prices = process_price_data("data/industrial_el_prices.csv") *1000
        if ctr_sel in industrial_prices:
            industrial_prices = pd.DataFrame(industrial_prices.loc[ctr_sel,:])
            industrial_prices["year"] = industrial_prices.index.to_series().str.extract(r"(\d{4})").astype(int)
            industrial_prices_avg = industrial_prices.groupby("year")[ctr_sel].mean()
            if year_sel in industrial_prices_avg:
                industrial_prices_avg = industrial_prices_avg.loc[year_sel]
                st.info(f"Average industrial electricity price from EUROSTAT for this year was: {industrial_prices_avg} EUR/MWh \n")

        if p_el_profiles.isna().sum().sum() > 1:
            st.warning(f"Electricity prices contains missing values. Don't trust the results.")

        p_el = [x for x in p_el_profiles.to_list() for _ in range(4)]
        p_el_f = st.number_input("Multiply electricity profile with...", value=1.0, min_value = 0.0, max_value = 10.0, step = 0.01)
        p_el = [p * p_el_f/1000 for p in p_el]

        st.info(f"Min electricity prices from profile is {round(np.min(p_el*1)*1000,0)} EUR/MWh.")
        st.info(f"Average electricity prices from profile is {round(np.mean(p_el)*1000,0)} EUR/MWh.")
        st.info(f"Max electricity prices from profile is {round(np.max(p_el)*1000,0)} EUR/MWh.")


    total_costs = pd.DataFrame(columns=['Allowable costs in EUR/kW'])
    for profile_name in st.session_state['demand_profiles'].keys():
        heat_demand = st.session_state['demand_profiles'][profile_name]["profile"]
        heat_demand["p_el"] = p_el[0:len(heat_demand)]
        T_l = st.session_state['demand_profiles'][profile_name]["T_l"]
        T_h = st.session_state['demand_profiles'][profile_name]["T_h"]
        cop = calculate_cop(T_l, T_h, exergetic_efficiency)

        delta_t = heat_demand["datetime"].diff().dropna().mode()[0].total_seconds() / 3600

        # cost alternative
        heat_demand["heat_consumption"] = heat_demand["demand"]*delta_t
        total_heat_demand = heat_demand["heat_consumption"].sum()
        total_cost_alternative = total_heat_demand * p_th

        # cost hp
        heat_demand["electricity_power"] = heat_demand["demand"] / cop
        heat_demand["electricity_consumption"] = heat_demand["electricity_power"]*delta_t
        heat_demand["electricity_costs"] = heat_demand["electricity_consumption"] * heat_demand["p_el"]

        total_cost_hp = heat_demand["electricity_costs"].sum()
        electric_capacity_hp = 1/cop
        f = calculate_annuity_factor(interest_rate, lifetime)
        allowable_costs = (total_cost_alternative - total_cost_hp) / electric_capacity_hp * f
        new_profile_name = profile_name + " " + str(int(T_l)) + "->" + str(int(T_h))
        total_costs.loc[new_profile_name,'Allowable costs in EUR/kW'] = allowable_costs

        # st.text(f"COP: {cop}")
        # st.text(f"Cost alternative: {total_cost_alternative}")
        # st.text(f"Cost heat pump: {total_cost_hp}")
        # st.text(f"Annualization factor: {f}")
        # st.text(f"Allowable cost: {allowable_costs}")



    # st.table(total_costs.reset_index())
    # st.markdown(f"Allowable hp costs in EUR/kW: {round(allowable_costs, 1)}")

    # st.table(total_costs)

    chart = (
        alt.Chart(total_costs.reset_index())
        .mark_bar(color="steelblue")
        .encode(
            y=alt.Y("index:N",
                    title=None,
                    sort="-x",
                    axis=alt.Axis(labelLimit=600)
                    ),
            x=alt.X("Allowable costs in EUR/kW:Q", title="Allowable costs (EUR/kW)"),
        )
        .properties(
            width=400,
            height=300,
            title="Allowable costs by process"
        )
    )

    st.altair_chart(chart, width='stretch')

