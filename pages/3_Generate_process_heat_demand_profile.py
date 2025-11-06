import streamlit as st
import pandas as pd
import altair as alt
from src import manage_cash
from src.profile_generation import *

manage_cash()

st.set_page_config(
    page_title="Heat demand profile",
)

# Application
st.markdown("**Application**")
T_l = st.number_input("Temperature of heat source in Celsius", value=30.0, min_value = -20.0, max_value = 150.0, step = 0.5)
T_h = st.number_input("Temperature of heat sink in Celsius", value=90.0, min_value = 0.0, max_value = 250.0, step = 0.5)

# Process specification
st.markdown("**Process specifications** ")
# Process type
profile_options = [
    "Batch process",
    "Continuous process",
]
process_type = st.selectbox(
    "What process would you like to look at?", profile_options
)

weekend_different = st.checkbox("Weekends different", value=False)

if weekend_different:
    weekend_scale = st.number_input("Scale weekends to x%", min_value=0, max_value=100, step=1)
else:
    weekend_scale = 1


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
df = generate_demand_profile_template(weekend_different, weekend_scale)

if process_type == "Batch process":
    df.loc[:, 'demand'] = generate_batch_process(hour_on, hour_off, length_on, length_off)

elif process_type == "Continuous process":
    df.loc[:, 'demand'] = generate_continuous_process(heat_demand["demand"].to_list())

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

st.markdown("**Save heat demand profile**")
profile_name = st.text_input("Profile name")
if st.button("Save heat demand profile"):
    if profile_name not in st.session_state['demand_profiles']:
        st.session_state['demand_profiles'][profile_name] = {"T_h": T_h, "T_l":T_l, "profile": df[["datetime", "demand"]]}
        st.markdown(f"{profile_name} saved")
    else:
        st.markdown(f"{profile_name} already exists")