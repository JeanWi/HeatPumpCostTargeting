import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List
import plotly.graph_objects as go

# Todo: add download link for filtered data
# Todo: short labels to long labels


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

if indicator == "Emissions":
    df.loc[df["Variable"] == "PROCESS_EMI", "Process"] = "Process Emissions"
    df.loc[df["Variable"] == "PROCESS_EMI", "End_use"] = "Process Emissions"
    df.loc[df["Variable"] == "PROCESS_EMI", "Fuel"] = "Process Emissions"

# Select year
years = sorted([int(y) for y in df["Year"].dropna().unique() if 1900 <= int(y) <= 2100])
year = st.select_slider("Year", options=years, value=years[-1])

# Filter
df_filtered = df[df["Year"] == int(year)]

# Select sector
sectors = sorted([s for s in df["Sector_long"].dropna().unique()])
sector = st.selectbox("Sector", ["All sectors"] + sectors)
if sector != "All sectors":
    df_filtered = df_filtered[df_filtered["Sector_long"] == sector]

# Select subsector
subsectors = sorted([s for s in df_filtered["Subsector"].dropna().unique()])
subsector = st.selectbox("Subsector", ["All subsectors"] + subsectors)
if subsector != "All subsectors":
    df_filtered = df_filtered[df_filtered["Subsector"] == subsector]

# Select process
processes = sorted([s for s in df_filtered["Process"].dropna().unique()])
process = st.selectbox("Process", ["All processes"] + processes)
if process != "All processes":
    df_filtered = df_filtered[df_filtered["Process"] == process]

# Select fuel
fuels = sorted([s for s in df_filtered["Fuel"].dropna().unique()])
fuel = st.selectbox("Fuel", ["All fuels"] + fuels)
if fuel != "All fuels":
    df_filtered = df_filtered[df_filtered["Fuel"] == fuel]


st.dataframe(df_filtered["Subsector"].unique())


fuel_colors = {
    # Natural / environment
    "AMBIENT": (192, 192, 192),
    "SOLAR_GEO": (255, 193, 7),

    # Biomass & waste (greenish)
    "BIOMASS_WASTE": (85,107,47),
    "DERIVED": (230,230,250),
    "NG_BIOGAS": (176,196,222),

    # Solids / coal-like (greyish)
    "COKE": (100, 100, 100),
    "NONCOKE_SOLIDS": (150, 150, 150),
    "SOLIDS": (224, 224, 224),

    # Liquid fossil fuels (brownish)
    "DIESEL_LIQBIO": (139,69,19),
    "RFO": (210,105,30),
    "RFG": (244,164,96),
    "LPG": (255,228,181),
    "NAPHTHA": (188,143,143),

    # Electricity / heat carriers (yellowish)
    "ELEC": (255,215,0),
    "STEAM_DISTR": (184,134,11),

    # Other (redish)
    "OTHER": (250,128,114),

    # Non-energy emissions
    "Process Emissions": (0, 0, 0),   # black
}

df_filtered["color"] = df_filtered["Fuel"].map(fuel_colors)

def plot_bar(row, fig, level):
    def rgb_tuple_to_plotly(rgb):
        return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    marker = dict(
        line=dict(color='ghostwhite', width=1)
    )

    showlegend = False
    legend_name = None

    if order_by == "Sectors":
        fuel = row.name[-1]
    else:
        fuel = row.name

    if fuel in fuel_colors:
        marker["color"] = rgb_tuple_to_plotly(fuel_colors[fuel])

        # show legend only once per fuel
        if fuel not in shown_legend_items:
            showlegend = True
            legend_name = fuel
            shown_legend_items.add(fuel)

    fig.add_trace(go.Bar(
        x=[row["Value"]],
        y=[level],
        orientation='h',
        marker=marker,
        name=legend_name,          # legend label
        legendgroup=legend_name,   # groups same fuel
        showlegend=showlegend,
        hovertemplate=(
            "Label: " + str(row.name) + "<br>"
            "Value: %{x:,.0f}<extra></extra>"
        ),
    ))

def filter_multiindex(df, key):
    # pad key with slice(None) to match index levels
    key_full = key + (slice(None),) * (df.index.nlevels - len(key))
    return df.loc[key_full]

def plot_sector_recursive(row, df_plot, fig, current_level, max_level):


    if current_level > max_level:
        return

    next_level = current_level + 1
    name_level = levels[current_level-1]
    plot_bar(row, fig, level=name_level)
    groupby_vars = levels[0:next_level]

    if isinstance(row.name, str):
        row.name = (row.name,)

    df_level_next_level = df_plot
    for col, val in zip(groupby_vars, row.name):
        df_level_next_level = df_level_next_level[df_plot[col] == val]

    df_level_next_level = df_level_next_level[groupby_vars + ["Value", "Code"]].groupby(groupby_vars).sum()

    for _, row_1 in df_level_next_level.iterrows():
        plot_sector_recursive(
            row=row_1,
            df_plot=df_plot,
            fig=fig,
            current_level=next_level,
            max_level=max_level,
        )


order_by = st.selectbox("Sort by", options=["Fuels", "Sectors"])

if order_by == "Fuels":
    levels = ["Fuel", "Sector_long", "Subsector", "Process", "End_use"]
else:
    levels = ["Sector_long", "Subsector", "Process", "End_use", "Fuel"]

fig = go.Figure()

start_level = 1
end_level = 5

shown_legend_items = set()
groupby_vars = levels[0:start_level]
df_first_level_aggregation = df_filtered[groupby_vars + ["Value", "Code"]].groupby(groupby_vars).sum()
for _, row in df_first_level_aggregation.iterrows():
    plot_sector_recursive(
        row=row,
        df_plot=df_filtered,
        fig=fig,
        current_level=start_level,
        max_level=end_level,
    )
















#
# df_first_level_aggregation = df_filtered[["Sector", "Value"]].groupby(["Sector"]).sum()
#
# for _, row in df_first_level_aggregation.iterrows():
#     plot_bar(row, fig, level="Sector")
#     sector = row.name
#     df_second_level = df_filtered[df_filtered["Sector"] == sector]
#     df_second_level_aggregation = df_second_level[["Subsector", "Value"]].groupby(["Subsector"]).sum()
#
#     for _, row in df_second_level_aggregation.iterrows():
#         plot_bar(row, fig, level="Sub sector")
#         process = row.name
#         df_third_level = df_filtered[df_filtered["Process"] == process]
#         df_third_level_aggregation = df_third_level[["Subsector", "Value"]].groupby(["Subsector"]).sum()
#
#         for _, row in df_second_level_aggregation.iterrows():
#             plot_bar(row, fig, level="Process")

fig.update_layout(
    barmode="stack",
    showlegend=True,
)

st.plotly_chart(fig, use_container_width=True)




#
# for level in sorted(df_filtered["Aggregation_level"].unique()):
#     df_plot = df_filtered[df_filtered["Aggregation_level"] == level]
#     st.write(level)
#     chart = (
#         alt.Chart(df_plot)
#         .mark_bar()
#         .encode(
#             x=alt.X("Value:Q"),
#             y="sub_sector:N",
#         )
#     )
#
#     st.altair_chart(chart, use_container_width=True)






















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