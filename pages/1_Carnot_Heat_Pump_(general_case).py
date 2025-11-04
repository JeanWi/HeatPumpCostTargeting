import streamlit as st
import numpy as np
import pandas as pd
import altair as alt


st.set_page_config(
    page_title="Carnot Heat Pump",
)

# hp_analysis_type = st.selectbox(label= "Select type of heat pump", options = ["Carnot Heat Pump"])
def calculate_profitable_relative_price(T_l, T_h, ex_eta=1):
    return (1 - (T_l + 273) / (T_h+ 273)) ** -1 * ex_eta

def get_relative_prices():
    def process_price_data(path):
        df = pd.read_csv(path, index_col=0).apply(pd.to_numeric, errors='coerce')
        df = df.dropna(axis=1, how='all')
        return df.dropna(axis=0, how='any')

    p_el = process_price_data("data/industrial_el_prices.csv")
    p_th = process_price_data("data/industrial_gas_prices.csv")
    p_rel = p_el.divide(p_th)
    return p_rel.dropna(axis=0, how='any')

relative_prices = get_relative_prices()

st.markdown("**Heat specifications**")
on_x_axis = st.selectbox("Plot on x axis", ["sink temperature", "source temperature"])

if on_x_axis == "sink temperature":
    T_l = st.number_input("Temperature of heat source in Celsius", value=15.0, min_value=-20.0, max_value=150.0,
                          step=0.5)
    x_settings = {
        "range": (int(T_l) + 20, 250),
        "arg": "T_h",
        "xlabel": "Sink temperature (°C)",
        "legend_title": f"Source temperature {round(T_l,1)}°C",
    }
    current_x = T_l
elif on_x_axis == "source temperature":
    T_h = st.number_input("Temperature of heat sink in Celsius", value=45.0, min_value=0.0, max_value=250.0, step=0.5)
    x_settings = {
        "range": (-10, int(T_h)-20),
        "arg": "T_l",
        "xlabel": "Source temperature (°C)",
        "legend_title": f"Sink temperature {round(T_h,1)}°C",
    }
    current_x = T_h

exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0, step=0.5)


st.markdown("**Relative electricity prices**")
plot_relative_prices_countries = st.multiselect("Show relative prices for the following regions: ", relative_prices.index)
plot_relative_prices_year = st.selectbox("Show relative prices for the following time: ", relative_prices.columns)

plot_price_data = relative_prices.loc[plot_relative_prices_countries, plot_relative_prices_year].reset_index()
plot_price_data.columns = ["Country", "Relative electricity price"]


num_points = 200

# Select configuration
cfg = x_settings
x_vals = np.linspace(*cfg["range"], num_points)

# Generate y values by substituting the swept parameter
def calc(x):
    return calculate_profitable_relative_price(
        T_l if cfg["arg"] != "T_l" else x,
        T_h if cfg["arg"] != "T_h" else x,
        exergetic_efficiency /100
    )

y_vals = [calc(x) for x in x_vals]
xlabel = cfg["xlabel"]

# --- Prepare data ---
data = pd.DataFrame({xlabel: x_vals, "Relative electricity price": y_vals})
data["Label"] = x_settings["legend_title"]

# st.table(data)

# Calculate current point NPV

x_limits = (min(current_x, min(x_vals))*0.9, max(current_x, max(x_vals))*1.1)
y_limits = (min(0, min(y_vals)), max(y_vals)*1.1)

# --- Plot ---
line = (
    alt.Chart(data)
    .mark_line()
    .encode(
        x=alt.X(f"{xlabel}:Q", title=xlabel).scale(domain=x_limits),
        y=alt.Y("Relative electricity price:Q", title="Relative electricity price").scale(domain=y_limits),
        tooltip=[xlabel, "Relative electricity price"]
    )
)

area = (
    alt.Chart(data)
    .mark_area(opacity=0.3, color="grey")
    .encode(
        x=alt.X(f"{xlabel}:Q", title=xlabel).scale(domain=x_limits),
        y=alt.Y("Relative electricity price:Q", title="Relative electricity price").scale(domain=y_limits),
        tooltip=[xlabel, "Relative electricity price"]
    )
)

vertical = (
    alt.Chart(pd.DataFrame({xlabel: [current_x]}))
    .mark_rule(color="black", strokeDash=[5, 5])
    .encode(x=alt.X(f"{xlabel}:Q").scale(domain=x_limits))
)

horizontal = (
    alt.Chart(plot_price_data)
    .mark_rule()
    .encode(
        y=alt.Y("Relative electricity price:Q", title="Relative electricity price"),
        color=alt.Color("Country", title="Relative electricity price"),
    )
    .properties(height=400, width=700)
)

text_data = pd.DataFrame({
    xlabel: [current_x],        # x-position
    "Relative electricity price": (y_limits[1] - y_limits[0]) * 0.95,  # y-position
    "label": [x_settings["legend_title"]]  # text to show
})

# text = (
#     alt.Chart(text_data)
#     .mark_text(
#         align='center',       # horizontal alignment: 'left', 'center', 'right'
#         baseline='middle',  # vertical alignment
#         dx=5,               # x-offset (in pixels)
#         dy=-5,              # y-offset
#         fontSize=12,
#         color='black'
#     )
#     .encode(
#         x=alt.X(f"{xlabel}:Q"),
#         y=alt.Y("Relative electricity price:Q"),
#         text="label:N"
#     )
# )


# Combine everything
chart = (area + line + vertical + horizontal).properties(
    height=400, width=700
).interactive()

st.altair_chart(chart, width='stretch')
# st.text(f"COP is {round((1 - T_l / T_h) ** -1,1)}")