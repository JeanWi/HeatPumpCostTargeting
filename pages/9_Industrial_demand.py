import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List
import altair as alt
import plotly.graph_objects as go

# Streamlit app for exploring the JRC-IDEES2023 industry long tables
DATA_DIR = Path("data/JRC-IDEES2023")
FILE_TEMPLATE = "jrc_idees_industry_long_{}.csv"


def list_countries() -> List[str]:
    """Discover available country codes from CSV filenames in DATA_DIR.
    """
    files = sorted(DATA_DIR.glob("jrc_idees_industry_long_*.csv"))
    codes: List[str] = []
    for f in files:
        stem = f.stem
        parts = stem.split("_")
        if len(parts) >= 5:
            code = parts[-1]
        else:
            code = stem.replace("jrc_idees_industry_long_", "")
        codes.append(code)
    return codes


@st.cache_data
def load_country_df(code: str) -> pd.DataFrame:
    path = DATA_DIR / FILE_TEMPLATE.format(code)
    df = pd.read_csv(path, low_memory=False)
    return df

# --- Streamlit UI ---
st.set_page_config(page_title="Industrial demand (JRC IDEES)", layout="wide")
st.title("JRC-IDEES2023 — Industry (long tables)")

# Select type
indicator_types = {
    "Final energy consumption": ("fec", "Energy consumption (ktoe)"),
    "Emissions": ("emi", "Detailed split of CO2 emissions by subsector (kt of CO2)")}
indicator = st.selectbox("Indicator", indicator_types.keys())


# Select country
countries = list_countries()
country = st.selectbox("Country", countries, index=countries.index("EU27"))

df = load_country_df(country)
df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(pd.Int64Dtype())
df = df[df["Type"] == indicator_types[indicator][0]]

# Select year
years = sorted([int(y) for y in df["Year"].dropna().unique() if 1900 <= int(y) <= 2100])
year = st.select_slider("Year", options=years, value=years[-1])

# Filter
df_filtered = df[df["Year"] == int(year)]

# Select variable
variable = indicator_types[indicator][1]
df_filtered = df_filtered[df_filtered["variable_type"] == variable]
df_filtered = df_filtered.reset_index(drop=True)

# Show table and basic aggregation
df_first_level_aggregation = df_filtered[["Sector_long", "Value"]].groupby(["Sector_long"]).sum()
df_first_level_aggregation["Check"] = False

st.header(f"{indicator} for {country} in {year} by sector")

df_by_sector = (
    df_filtered[["Sector_long", "Value"]]
    .groupby("Sector_long", as_index=False)
    .sum()
    .sort_values("Value", ascending=False)
)

bar = (
    alt.Chart(df_by_sector)
    .mark_bar()
    .encode(
        x=alt.X("Value:Q", title="Value"),
        y=alt.Y("Sector_long:N", sort="-x", title="Sector"),
        tooltip=[
            alt.Tooltip("Sector_long:N", title="Sector"),
            alt.Tooltip("Value:Q", format=",.2f"),
        ],
    )
    .properties(height=400)
)

st.altair_chart(bar, use_container_width=True)


# Select sector
sectors = sorted([s for s in df["Sector_long"].dropna().unique()])
sector = st.selectbox("Sector", ["All sectors"] + sectors)
if sector != "All sectors":
    df_filtered = df_filtered[df_filtered["Sector_long"] == sector]


totals = df_filtered.groupby("sub_sector", as_index=False)["Value"].sum()
totals = totals.sort_values("Value", ascending=False)

# make ordered categorical
df_filtered["sub_sector_ordered"] = pd.Categorical(
    df_filtered["sub_sector"],
    categories=totals["sub_sector"],
    ordered=True
)

# stacked bar
stacked_bar = (
    alt.Chart(df_filtered)
    .mark_bar()
    .encode(
        x=alt.X("Value:Q", stack="zero", title="Value"),
        y=alt.Y("sub_sector_ordered:N", title="Sub-sector"),
        color=alt.Color("fuel_type:N", title="Fuel type"),
        tooltip=[
            alt.Tooltip("sub_sector:N", title="Sub-sector"),
            alt.Tooltip("fuel_type:N", title="Fuel type"),
            alt.Tooltip("level_3:N", title="Sub process"),
            alt.Tooltip("Value:Q", format=",.2f"),
        ],
    )
    .properties(height=400)
)

st.altair_chart(stacked_bar, use_container_width=True)


#
# # st.dataframe(df_first_level_aggregation)
#
# def plot_bar(row, fig, level):
#     # def rgb_tuple_to_plotly(rgb):
#     #     if rgb is None or (isinstance(rgb, float) and np.isnan(rgb)):
#     #         return "gray"
#     #     else:
#     #         return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
#
#     # st.write(row)
#     fig.add_trace(go.Bar(
#         x=[row["Value"]], y=[level],
#         orientation='h',
#         # marker=dict(
#         #     color=rgb_tuple_to_plotly(row["color"]),
#         #     line=dict(color='ghostwhite', width=1)
#         # ),
#         hovertemplate=(
#             "Label: " + str(row.name) + "<br>"
#             "Value: %{x:,.0f}<extra></extra>"
#         ),
#     ))
#
#
# fig = go.Figure()
# df_first_level_aggregation = df_filtered[["Sector_long", "Value"]].groupby(["Sector_long"]).sum()
#
# for _, row in df_first_level_aggregation.iterrows():
#     plot_bar(row, fig, level="Sector")
#     sector = row.name
#     df_second_level = df_filtered[df_filtered["Sector_long"] == sector]
#     df_second_level_aggregation = df_second_level[["sub_sector", "Value"]].groupby(["sub_sector"]).sum()
#
#     for _, row in df_second_level_aggregation.iterrows():
#         plot_bar(row, fig, level="Sub sector")
#
# fig.update_layout(
#     barmode="stack",
#     showlegend=False,
# )
#
# st.plotly_chart(fig, use_container_width=True)
#
#
#
#
# #
# # for level in sorted(df_filtered["Aggregation_level"].unique()):
# #     df_plot = df_filtered[df_filtered["Aggregation_level"] == level]
# #     st.write(level)
# #     chart = (
# #         alt.Chart(df_plot)
# #         .mark_bar()
# #         .encode(
# #             x=alt.X("Value:Q"),
# #             y="sub_sector:N",
# #         )
# #     )
# #
# #     st.altair_chart(chart, use_container_width=True)
#
#
#
#
#

















#
# def add_missing_values(totals, child_sectors, aggregation_level, label_name):
#     missing = totals - child_sectors["Value"].sum()
#     if missing > 0.01:
#         child_sectors = pd.concat([
#             child_sectors,
#             pd.DataFrame([{
#                 "Label": label_name,
#                 "Aggregation_level": aggregation_level,
#                 "Value": missing,
#             }])
#         ], ignore_index=True)
#     return child_sectors
#
# def plot_sector_recursive(row, df_plot, fig, current_level, max_level, trace_lookup):
#
#     next_level = current_level + 1
#     if current_level > max_level:
#         return
#
#     plot_bar(row, fig, trace_lookup)
#     total_emissions = row["Value"]
#     df_level_next_level = df_plot[df_plot["Parent_label"] == row["Label"]]
#     # df_level_next_level = set_colors(df_level_next_level, row["color"])
#     df_level_next_level = add_missing_values(total_emissions, df_level_next_level, next_level, row["Label"])
#     for _, row_next_level in df_level_next_level[df_level_next_level["Aggregation_level"] == next_level].iterrows():
#         plot_sector_recursive(
#             row=row_next_level,
#             df_plot=df_plot,
#             fig=fig,
#             current_level=next_level,
#             max_level=max_level,
#             trace_lookup = trace_lookup
#         )
#
# current_level = 1
# start_level = current_level + 1
# end_level = 5
# trace_lookup = []
#
# fig = go.Figure()
# for _, row in df_filtered[df_filtered["Aggregation_level"] == start_level].iterrows():
#     plot_sector_recursive(
#         row=row,
#         df_plot=df_filtered,
#         fig=fig,
#         current_level=start_level,
#         max_level=end_level,
#         trace_lookup = trace_lookup
#     )
#
# fig.update_layout(
#     barmode="stack",
#     showlegend=False,
# )
#
# st.plotly_chart(fig, use_container_width=True)