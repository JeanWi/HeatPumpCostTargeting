import pandas as pd
import altair as alt
import streamlit as st

from src.price_profile_generation import fit_electricty_price_trends, generate_electricity_price_profile, \
    load_electricity_price_profile

# st.markdown("**Select country and year to produce synthetic electricity price profile**")
# ctrs_available = [f.replace(".csv", "") for f in os.listdir("data/european_wholesale_electricity_price_data_hourly") if f.endswith(".csv")]
# ctr_sel = st.selectbox("Use price from country", ctrs_available)

ctr_sel = "Germany"
selected_years = 2024

p = load_electricity_price_profile(ctr_sel)
# selected_years = st.selectbox("Select a year:", set(p.index.year.to_list()))
p, params = fit_electricty_price_trends(p, selected_years)

st.markdown("**Scale profile**  \n The tool used electricity price information of Germany from 2025 and generates "
            "generic profiles based on https://www.sciencedirect.com/science/article/pii/S0140988311001721#f0015")
average_electricity_price = st.number_input("Average electricity price (EUR/MWh)", min_value=-500, max_value=500, step=1, value=0)

col1, col2 = st.columns(2)
with col1:
    trend_factor = st.number_input("Trend factor", min_value=0.0, max_value=10.0, step=0.1, value =1.0)
    weekly_factor = st.number_input("Weekly cycle scaling factor", min_value=0.0, max_value=10.0, step=0.1, value =1.0)
with col2:
    hourly_factor = st.number_input("Daily cycle scaling factor", min_value=0.0, max_value=10.0, step=0.1, value =1.0)
    overall_factor = st.number_input("Overall profile scaling factor", min_value=0.0, max_value=10.0, step=0.1, value =1.0)

scaling_factors = {
    "trend": trend_factor,
    "weekly_factor": weekly_factor,
    "hourly_factor": hourly_factor,
    "overall_factor":overall_factor
}

p_gen = generate_electricity_price_profile(params, average_electricity_price, scaling_factors, selected_years)

min_time = p_gen.index.min()
max_time = p_gen.index.max()

start, end = st.slider(
    "Select time range",
    min_value=min_time.to_pydatetime(),
    max_value=max_time.to_pydatetime(),
    value=(min_time.to_pydatetime(), max_time.to_pydatetime()),
)


p_gen_plot = p_gen["p"]
p_gen_plot.index.name = None
p_gen_plot.name = "Generic price profile"
p_gen_plot = p_gen_plot.to_frame(name="p").assign(source=p_gen_plot.name)

p_de_plot = p["p"]
p_de_plot.index.name = None
p_de_plot.name = "Actual German price profile (2024)"
p_de_plot  = p_de_plot.to_frame(name="p").assign(source=p_de_plot.name)

p_plot = pd.concat([p_de_plot, p_gen_plot])

p_plot_sel = p_plot[(p_plot.index >= start) & (p_plot.index <= end)]

chart = (
    alt.Chart(p_plot_sel.reset_index())
    .mark_line()
    .encode(
        x=alt.X("index:T", title="Time"),
        y=alt.Y("p:Q", title="Electricity Price (EUR/MWh)"),
        color=alt.Color(
            "source:N",
            title="Price profile",
            scale=alt.Scale(
                range=["crimson", "steelblue"]  # choose any colors
            )
        )
    )
    .interactive()
)

st.altair_chart(chart, width='stretch')
