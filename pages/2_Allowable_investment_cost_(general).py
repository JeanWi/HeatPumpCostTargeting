import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

from src import manage_cash
from src.carnot_hp_calculations import calculate_allowable_investment_per_kw_el

manage_cash()
st.set_page_config(
    page_title="Carnot Heat Pump",
)

# hp_analysis_type = st.selectbox(label= "Select type of heat pump", options = ["Carnot Heat Pump"])

st.markdown("**Application**")
T_l = st.number_input("Temperature of heat source in Celsius", value=30.0, min_value = -20.0, max_value = 150.0, step = 0.5)
T_h = st.number_input("Temperature of heat sink in Celsius", value=90.0, min_value = 0.0, max_value = 250.0, step = 0.5)
operating_hours = st.number_input("Operating hours per year", value=6000, min_value = 0, max_value = 8760, step = 1)
exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0, step=0.5)

st.markdown("**Alternative heat provision**")
p_th = st.number_input("Cost of alternative heat provision (EUR/MW)", value=50, min_value = 0, max_value = 300)

st.markdown("**Electricity price**")
p_el = st.number_input("Cost of electricity for heat pump (EUR/MW)", value=150, min_value = 0, max_value = 300)

st.markdown("**Economic assumptions**")
lifetime = st.number_input("Lifetime of heat pump", value=15, min_value = 0, max_value = 100)
interest_rate = st.number_input("Interest rate", value=5.0, min_value = 0.1, max_value = 20.0)

st.markdown("**Plotting options**")
num_points = 200

# Define variable sweep settings
x_settings = {
    "electricity price": {
        "range": (p_el-50, p_el+50),
        "arg": "p_el",
        "xlabel": "Electricity price (EUR/kW)",
        "x_current": p_el
    },
    "heat provision cost of alternative": {
        "range": (p_th-50, p_th+50),
        "arg": "p_th",
        "xlabel": "Alternative heat provision cost (EUR/kW)",
        "x_current": p_th
    },
    "sink temperature": {
        "range": (int(T_l)+20, 250),
        "arg": "T_h",
        "xlabel": "Sink temperature (°C)",
        "x_current": T_h
    },
    "source temperature": {
        "range": (-10, int(T_h)-20),
        "arg": "T_l",
        "xlabel": "Source temperature (°C)",
        "x_current": T_l
    },
    "operating hours": {
        "range": (operating_hours-1000, operating_hours+1000),
        "arg": "operating_hours",
        "xlabel": "Operating hours per year",
        "x_current": operating_hours
    },
    "interest rate": {
        "range": (interest_rate-0.1, interest_rate+0.1),
        "arg": "interest_rate",
        "xlabel": "Interest rate (-)",
        "x_current": interest_rate
    },
    "lifetime": {
        "range": (lifetime-10, lifetime+10),
        "arg": "lifetime",
        "xlabel": "Lifetime (years)",
        "x_current": lifetime
    },
    "exergetic efficiency": {
        "range": (0, 100),
        "arg": "exergetic efficiency",
        "xlabel": "exergetic efficiency (%)",
        "x_current": exergetic_efficiency
    },
}
on_x_axis = st.selectbox("Plot on x axis", x_settings.keys())


# Select configuration
cfg = x_settings[on_x_axis]
x_vals = np.linspace(*cfg["range"], num_points)

# Generate y values by substituting the swept parameter
def calc(x):
    return calculate_allowable_investment_per_kw_el(
        T_l if cfg["arg"] != "T_l" else x,
        T_h if cfg["arg"] != "T_h" else x,
        operating_hours if cfg["arg"] != "operating_hours" else x,
        p_th if cfg["arg"] != "p_th" else x,
        p_el if cfg["arg"] != "p_el" else x,
        interest_rate/100 if cfg["arg"] != "interest_rate" else x/100,
        lifetime if cfg["arg"] != "lifetime" else x,
        exergetic_efficiency/100 if cfg["arg"] != "exergetic efficiency" else x/100,
    )

y_vals = [calc(x) for x in x_vals]

# st.text(cfg["arg"])
# st.table(x_vals)
# st.table(y_vals)

x_current = cfg["x_current"]
xlabel = cfg["xlabel"]

y_current = calculate_allowable_investment_per_kw_el(T_l, T_h, operating_hours, p_th, p_el, interest_rate/100, lifetime, exergetic_efficiency / 100)

# --- Prepare data ---
data = pd.DataFrame({xlabel: x_vals, "NPV (EUR/kW)": y_vals})

# Calculate current point NPV
npv_current = calculate_allowable_investment_per_kw_el(T_l, T_h, operating_hours, p_th, p_el, interest_rate/100, lifetime, exergetic_efficiency / 100)

x_limits = (min(x_vals), max(x_vals))
y_limits = (min(0, min(y_vals)), max(y_vals)*1.1)

# --- Plot ---
line = (
    alt.Chart(data)
    .mark_line()
    .encode(
        x=alt.X(f"{xlabel}:Q", title=xlabel).scale(domain=x_limits),
        y=alt.Y("NPV (EUR/kW):Q", title="Allowable CAPEX (EUR/kW)").scale(domain=y_limits),
        tooltip=[xlabel, "NPV (EUR/kW):Q"]
    )
)

point = (
    alt.Chart(pd.DataFrame({xlabel: [x_current], "NPV (EUR/kW)": [npv_current]}))
    .mark_point(size=100, color="red")
    .encode(
        x=alt.X(f"{xlabel}:Q").scale(domain=x_limits),
        y=alt.Y("NPV (EUR/kW):Q", title="Allowable CAPEX (EUR/kW)").scale(domain=y_limits),
        tooltip=[xlabel, "NPV (EUR/kW)"]
    )
)

current1 = (
    alt.Chart(pd.DataFrame({xlabel: [x_current]}))
    .mark_rule(color="black", strokeDash=[5, 5])
    .encode(x=alt.X(f"{xlabel}:Q").scale(domain=x_limits))
)

current2 = (
    alt.Chart(pd.DataFrame({"NPV (EUR/kW)": [y_current]}))
    .mark_rule(color="black", strokeDash=[5, 5])
    .encode(y=alt.Y("NPV (EUR/kW):Q", title="Allowable CAPEX (EUR/kW)").scale(domain=y_limits))
)

y_min, y_max = 1200, 10e6

# Create shaded area spanning full x range
area = (
    alt.Chart(pd.DataFrame({"y_min": [y_min], "y_max": [y_max]}))
    .mark_rect(opacity=0.2, color="grey")
    .encode(
        y=alt.Y("y_min:Q", title="Allowable CAPEX (EUR/kW)").scale(domain=y_limits),
        y2="y_max:Q"
    )
)

# Combine everything
st.text("Grey area is reasonable industrial heat pump cost from literature")
chart = (area + line + point + current1 + current2).properties(
    height=400, width=700
).interactive()

st.altair_chart(chart, width='stretch')
# st.text(f"COP is {round((1 - T_l / T_h) ** -1,1)}")