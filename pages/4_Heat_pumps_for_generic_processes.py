import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

st.set_page_config(
    page_title="Carnot Heat Pump",
)

# hp_analysis_type = st.selectbox(label= "Select type of heat pump", options = ["Carnot Heat Pump"])

def calculate_allowable_investment_per_kw_el(T_l, T_h, h, p_th, p_el, r, t, ex_eta=1):
    r = r/ 100
    cop = (1 - (T_l + 273) / (T_h+ 273)) ** -1 * ex_eta
    f = ((1-(1/(1+r)**t))/r)
    return (p_th*cop/1000 - p_el/1000) * h * f

st.markdown("**Process specifications**  \nGenerates the heat demand profile")
# Process type
profile_options = [
    "Batch process",
    "Continuous process",
]
process_type = st.selectbox(
    "What process would you like to look at?", profile_options
)




weekends_different = st.checkbox("Weekends different", value=False)

if weekends_different:
    weekend_scale = st.number_input("Scale weekends to x%", min_value=0, max_value=100, step=1)


# Options
if process_type == "Continuous process":
    variation_during_day = st.checkbox("Variations during the day", value=False)

    date_rng = pd.date_range(start='2025-01-01', end='2025-01-01 23:45:00', freq='60min')
    demand_cp = pd.DataFrame(date_rng, columns=['datetime'])
    demand_cp['demand'] = 1.0

    if variation_during_day:
        heat_demand = st.data_editor(
            demand_cp,
            column_config={
                'demand': st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=1.0,
                    help="Enter a value between 0.0 and 1.0",
                )
            }
        )
    else:
        heat_demand = demand_cp

elif process_type == "Batch process":
    col1, col2 = st.columns(2)
    with col1:
        length_on = st.number_input("Duration of process in h", min_value=0.0, max_value=24.0, step=0.25, value=1.0)
        hour_on = st.number_input("Hour of day when process starts", min_value=0.0, max_value=24.0, step=0.25, value=0.0)
    with col2:
        length_off = st.number_input("Pause between batches in h", min_value=0.0, max_value=24.0, step=0.25, value=1.0)
        hour_off = st.number_input("Hour of day when process stops", min_value=0.0, max_value=24.0, step=0.25, value=24.0)

# Generate process
date_rng = pd.date_range(start='2025-01-01', end='2025-12-31 23:45:00', freq='15min')
df = pd.DataFrame(date_rng, columns=['datetime'])
df['demand'] = 0
df['day_of_week'] = df['datetime'].dt.dayofweek
df['scaled_process'] = 1
if weekends_different:
    df['scaled_process'] = df['day_of_week'].isin([5, 6]).apply(lambda x: weekend_scale / 100 if x else 1)

if process_type == "Batch process":
    available_time_per_day = hour_off - hour_on
    batches_per_day = available_time_per_day/(length_off+length_on)

    profile_one_batch = [1] * int(length_on * 4) + [0] * int(length_off * 4)
    profile_n_batches = profile_one_batch * math.floor(batches_per_day)
    profile_day_beginning = [0] * int(hour_on * 4) + profile_n_batches
    hours_missing = 24*4 - len(profile_day_beginning)
    profile_day = profile_day_beginning + [0]*int(hours_missing)
    profile_week = profile_day * 7
    profile_year = profile_day * 365

    df.loc[:, 'demand'] = profile_year

elif process_type == "Continuous process":
    profile_day = [x for x in heat_demand["demand"].to_list() for _ in range(4)]
    profile_week = profile_day * 7
    profile_year = profile_day * 365

    df.loc[:, 'demand'] = profile_year

df['demand'] = df['demand'] * df['scaled_process']


# Plot only...
plotting_options = st.selectbox("Plot...", ["Full week", "Weekend", "Weekday"])
if plotting_options == "Full week":
    first = df.loc[df['datetime'].dt.weekday == 0, 'datetime'].iloc[0].normalize()
    last = first + pd.Timedelta(days=6, hours=23, minutes=45)
elif plotting_options == "Weekend":
    first = df.loc[df['datetime'].dt.weekday == 5, 'datetime'].iloc[0].normalize()
    last = first + pd.Timedelta(days=1, hours=23, minutes=45)
elif plotting_options == "Weekday":
    first = df.loc[df['datetime'].dt.weekday == 1, 'datetime'].iloc[0].normalize()
    last = first + pd.Timedelta(days=0, hours=23, minutes=45)

df_plot = df[(df['datetime'] >= first) & (df['datetime'] <= last)]


y_limits = (0, 1.1)
line = (
    alt.Chart(df_plot)
    .mark_line()
    .encode(
        x=alt.X(f"datetime:T", title="Time"),
        y=alt.Y("demand:Q", title="Heat demand").scale(domain=y_limits)
    )
)

chart = (line).properties(
    height=400, width=700
).interactive()

st.altair_chart(chart, width='stretch')