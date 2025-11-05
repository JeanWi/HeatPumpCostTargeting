import pandas as pd
import streamlit as st
from src import manage_cash
import altair as alt

manage_cash()

def calculate_cop(T_l, T_h, ex_eta=1):
    return (1 - (T_l + 273) / (T_h+ 273)) ** -1 * ex_eta
def calculate_annuity_factor(r, t):
    return (1-(1/(1+r)**t))/r

st.markdown("**Application**")
# profile_name = st.selectbox("Select previously saved heat demand profile", )
T_l = st.number_input("Temperature of heat source in Celsius", value=30.0, min_value = -20.0, max_value = 150.0, step = 0.5)
T_h = st.number_input("Temperature of heat sink in Celsius", value=90.0, min_value = 0.0, max_value = 250.0, step = 0.5)

st.markdown("**Heat pump specs**")
exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0, step=0.5) /100
cop = calculate_cop(T_l, T_h, exergetic_efficiency)
lifetime = st.number_input("Lifetime of heat pump", value=15, min_value = 0, max_value = 100)
interest_rate = st.number_input("Interest rate", value=5.0, min_value = 0.1, max_value = 20.0) / 100

st.markdown("**Alternative heat provision**")
p_th = st.number_input("Cost of alternative heat provision (EUR/MWth)", value=50, min_value = 0, max_value = 300)/1000

st.markdown("**Electricity price**")
p_el = st.number_input("Cost of electricity for heat pump (EUR/MWel)", value=150, min_value = 0, max_value = 300)/1000

total_costs = pd.DataFrame(columns=['Allowable costs in EUR/kW'])
for profile_name in st.session_state['demand_profiles'].keys():
    heat_demand = st.session_state['demand_profiles'][profile_name]
    total_heat_demand = heat_demand["demand"].sum()
    total_cost_alternative = total_heat_demand * p_th
    total_cost_hp = total_heat_demand / cop * p_el
    electric_capacity_hp = 1/cop
    f = calculate_annuity_factor(interest_rate, lifetime)
    allowable_costs = (total_cost_alternative - total_cost_hp) / electric_capacity_hp * f
    total_costs.loc[profile_name,'Allowable costs in EUR/kW'] = allowable_costs

    # st.text(f"COP: {cop}")
    # st.text(f"Cost alternative: {total_cost_alternative}")
    # st.text(f"Cost heat pump: {total_cost_hp}")
    # st.text(f"Annualization factor: {f}")
    # st.text(f"Allowable cost: {allowable_costs}")



# st.table(total_costs.reset_index())
# st.markdown(f"Allowable hp costs in EUR/kW: {round(allowable_costs, 1)}")

chart = (
    alt.Chart(total_costs.reset_index())
    .mark_bar(color="steelblue")
    .encode(
        y=alt.Y("index:N", title=None, sort="-y"),
        x=alt.X("Allowable costs in EUR/kW:Q", title="Allowable costs (EUR/kW)"),
    )
    .properties(
        width=400,
        height=300,
        title="Allowable costs by process"
    )
)

st.altair_chart(chart, width='stretch')

