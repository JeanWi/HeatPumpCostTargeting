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
    "Final energy consumption": "fec",
   "Useful energy demand": "ued",
    "Emissions": "emi"}
indicator = st.selectbox("Indicator", indicator_types.keys())


# Select country
countries = list_countries()
country = st.selectbox("Country", countries, index=countries.index("EU27"))

df = load_country_df(country)
df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(pd.Int64Dtype())
df = df[df["Type"] == indicator_types[indicator]]

# Select year
years = sorted([int(y) for y in df["Year"].dropna().unique() if 1900 <= int(y) <= 2100])
year = st.select_slider("Year", options=years, value=years[-1])

# Select sector
sectors = sorted([s for s in df["Sector_long"].dropna().unique()])
sector = st.selectbox("Sector (Sector_long)", ["All sectors"] + sectors)

# Filter
df_filtered = df[df["Year"] == int(year)]
if sector != "All sectors":
    df_filtered = df_filtered[df_filtered["Sector_long"] == sector]

# Select variable
variables = [s for s in df_filtered["variable_type"].dropna().unique()]
variable = st.selectbox("Sector variable", variables)
df_filtered = df_filtered[df_filtered["variable_type"] == variable]
df_filtered = df_filtered.reset_index(drop=True)

# Show table and basic aggregation
st.dataframe(df_filtered)

df_first_level_aggregation = df_filtered[["Sector_long", "Value"]].groupby(["Sector_long"]).sum()
df_first_level_aggregation["Check"] = False

edited_df = st.data_editor(df_first_level_aggregation)
# st.dataframe(df_first_level_aggregation)
st.dataframe(df_first_level_aggregation.sum())






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





















def plot_bar(row, fig, trace_lookup):
    # def rgb_tuple_to_plotly(rgb):
    #     if rgb is None or (isinstance(rgb, float) and np.isnan(rgb)):
    #         return "gray"
    #     else:
    #         return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    # st.write(row)
    fig.add_trace(go.Bar(
        x=[row["Value"]], y=[row["Aggregation_level"]],
        orientation='h',
        customdata=[[row["Label"], row["Aggregation_level"]]],
        # marker=dict(
        #     color=rgb_tuple_to_plotly(row["color"]),
        #     line=dict(color='ghostwhite', width=1)
        # ),
        hovertemplate=(
            "Label: " + str(row["Label"]) + "<br>"
            "Value: %{x:,.0f}<extra></extra>"
        ),
    ))

    trace_lookup.append({
        "Sector_code": row["Label"],
        "aggregation_level": row["Aggregation_level"],
        "Parent_label": row["Parent_label"],
    })

def add_missing_values(totals, child_sectors, aggregation_level, label_name):
    missing = totals - child_sectors["Value"].sum()
    if missing > 0.01:
        child_sectors = pd.concat([
            child_sectors,
            pd.DataFrame([{
                "Label": label_name,
                "Aggregation_level": aggregation_level,
                "Value": missing,
            }])
        ], ignore_index=True)
    return child_sectors

def plot_sector_recursive(row, df_plot, fig, current_level, max_level, trace_lookup):

    next_level = current_level + 1
    if current_level > max_level:
        return

    plot_bar(row, fig, trace_lookup)
    total_emissions = row["Value"]
    df_level_next_level = df_plot[df_plot["Parent_label"] == row["Label"]]
    # df_level_next_level = set_colors(df_level_next_level, row["color"])
    df_level_next_level = add_missing_values(total_emissions, df_level_next_level, next_level, row["Label"])
    for _, row_next_level in df_level_next_level[df_level_next_level["Aggregation_level"] == next_level].iterrows():
        plot_sector_recursive(
            row=row_next_level,
            df_plot=df_plot,
            fig=fig,
            current_level=next_level,
            max_level=max_level,
            trace_lookup = trace_lookup
        )

current_level = 1
start_level = current_level + 1
end_level = 5
trace_lookup = []

fig = go.Figure()
for _, row in df_filtered[df_filtered["Aggregation_level"] == start_level].iterrows():
    plot_sector_recursive(
        row=row,
        df_plot=df_filtered,
        fig=fig,
        current_level=start_level,
        max_level=end_level,
        trace_lookup = trace_lookup
    )

fig.update_layout(
    barmode="stack",
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)