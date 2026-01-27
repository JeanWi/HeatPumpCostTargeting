import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

from src.industrial_heat_demand import get_color, plot_sector_recursive

if "filtered" not in st.session_state:
    st.session_state.current_sector = None
    st.session_state.current_level = 1
    st.session_state.filtered = False

if st.button("Reset Zoom"):
    st.session_state.current_sector = None
    st.session_state.current_level = 1
    st.session_state.filtered = False

all_emissions = pd.read_csv("data/emissions_europe/UNFCCC.csv", header=0, index_col=None, sep=",")
all_emissions = all_emissions[~all_emissions["Sector_code"].isin(["Sectors/Totals_excl", "Sectors/Totals_incl", "ind_CO2"])]
all_emissions["Parent_sector_code"] = all_emissions["Parent_sector_code"].replace("1.AA", "1.A")
all_emissions["Parent_sector_code"] = all_emissions["Parent_sector_code"].replace("3.1", "3")
all_emissions["emissions"].fillna(0, inplace=True)

# Sectors
sectors = all_emissions[["Sector_code", "Sector_name"]].drop_duplicates(inplace=False)
split_cols = sectors["Sector_code"].str.split(".", expand=True)
levels = split_cols.shape[1]
split_cols.columns = [f"Subsector{i+1}" for i in range(levels)]
sectors = pd.concat([sectors, split_cols], axis=1)
sectors["aggregation_level"] = levels - sectors.isna().sum(axis=1)

# Selections
countries = all_emissions["Country"].unique().tolist()
pollutant = all_emissions["Pollutant_name"].unique().tolist()
years = all_emissions["Year"].unique().tolist()

countries.sort()
pollutant.sort()
years.sort()

country_selected = st.selectbox("Select countries", countries)
pollutant_selected = st.selectbox("Select pollutants", pollutant)
year_selected = st.selectbox("Select years", years)

all_emissions_filtered = all_emissions[(all_emissions["Country"] == country_selected) &
                                        (all_emissions["Pollutant_name"] == pollutant_selected) &
                                        (all_emissions["Year"] == year_selected)]

all_emissions_filtered = all_emissions_filtered[['Sector_code', 'Parent_sector_code', 'emissions']]
all_emissions_filtered = pd.merge(all_emissions_filtered, sectors, on="Sector_code", how="left")
all_emissions_filtered = all_emissions_filtered[~all_emissions_filtered["Subsector1"].str.contains("4")]

df = all_emissions_filtered.copy()

children_sum = (
    df.groupby("Parent_sector_code")["emissions"]
    .sum(min_count=1)
    .rename("children_emissions")
)
df = df.merge(
    children_sum,
    left_on="Sector_code",
    right_index=True,
    how="left"
)
df["missing_emissions"] = df["emissions"] - df["children_emissions"]
df["missing_emissions"] = df["missing_emissions"].where(
    df["missing_emissions"] > 1e-3, 0
)
df["is_missing"] = False

missing_rows = df[df["missing_emissions"] > 0].copy()
missing_rows["Sector_code"] = missing_rows["Sector_code"] + "_missing"
missing_rows["Sector_name"] = missing_rows["Sector_name"] + " (unallocated)"
missing_rows["emissions"] = missing_rows["missing_emissions"]
missing_rows["is_missing"] = True
df = pd.concat([df, missing_rows], ignore_index=True)


BASE_COLORS = [
    "#1f77b4",  # blue
    "#9467bd",  # purple
    "#2ca02c",  # green
    "#d62728",  # red
]

# Color map for top level
top_sectors = (
    df[df["aggregation_level"] == 1]["Sector_code"]
    .unique()
)

top_color_map = {
    s: BASE_COLORS[i % len(BASE_COLORS)]
    for i, s in enumerate(top_sectors)
}

df["color"] = df.apply(get_color, axis=1, top_color_map=top_color_map)


# ---- Zoom / collapse ----
current_sector = st.session_state.current_sector
current_level = st.session_state.current_level
st.write(current_sector, current_level)


df_plot = df

df_plot = df_plot.sort_values(
    ["aggregation_level", "emissions"],
    ascending=[True, False]
)


levels = sorted(df_plot["aggregation_level"].unique())

df_plot = df_plot.sort_values(
    ["aggregation_level", "emissions"],
    ascending=[True, False]
)

if st.session_state.filtered:
    df_plot = df_plot[df_plot["Parent_sector_code"] == current_sector]


y_labels = df_plot["Sector_name"]
levels.reverse()

fig = go.Figure()

start_level = current_level + 1
end_level = 5
trace_lookup = []

for _, row_1 in df_plot[df_plot["aggregation_level"] == start_level].iterrows():
    plot_sector_recursive(
        row=row_1,
        df_plot=df_plot,
        fig=fig,
        current_level=start_level,
        max_level=end_level,
        trace_lookup = trace_lookup
    )

fig.update_layout(
    barmode="stack",
    showlegend=False,
    clickmode="event+select",
)

# st.plotly_chart(fig, use_container_width=True)
selected = plotly_events(fig, click_event=True)

if selected:
    clicked = trace_lookup[selected[0]["curveNumber"]]
    st.session_state.current_sector = clicked["Sector_code"]
    st.session_state.current_level = clicked["aggregation_level"]
    st.session_state.filtered = True

