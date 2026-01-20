import pandas as pd
import streamlit as st
import altair as alt

all_emissions = pd.read_csv("data/emissions_europe/UNFCCC.csv", header=0, index_col=None, sep=",")
all_emissions = all_emissions[~all_emissions["Sector_code"].isin(["Sectors/Totals_excl", "Sectors/Totals_incl", "ind_CO2"])]

# Split sectors
split_cols = all_emissions["Sector_code"].str.split(".", expand=True)
levels = split_cols.shape[1]
split_cols.columns = [f"Subsector{i+1}" for i in range(levels)]

# Drop sectors

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

sectors_on_level = {}
sectors_on_level[1] = split_cols["Subsector1"].unique().tolist()
sectors_on_level[2] =  (split_cols["Subsector1"] + "." + split_cols["Subsector2"]).unique().tolist()
sectors_on_level[3] =  (split_cols["Subsector1"] + "." + split_cols["Subsector2"] + "." + split_cols["Subsector3"]).unique().tolist()
sectors_on_level[4]  =  (split_cols["Subsector1"] + "." + split_cols["Subsector2"] + "." + split_cols["Subsector3"] + "." + split_cols["Subsector4"]).unique().tolist()

for level in sectors_on_level:
    for sector in sectors_on_level[level]:
        emissions_sector = all_emissions_filtered[all_emissions_filtered["Sector_code"] == sector]["emissions"].sum()
        emissions_subssectors = all_emissions_filtered[all_emissions_filtered["Parent_sector_code"] == sector]["emissions"].sum()
        parent_sector = all_emissions_filtered[all_emissions_filtered["Sector_code"] == sector]["Parent_sector_code"].values[0]
        delta_emissions = emissions_sector - emissions_subssectors
        if abs((delta_emissions)/emissions_sector) > 0.01:
            print(f"Warning: Emissions do not match for sector {sector}: sector emissions = {emissions_sector}, sum subsectors = {emissions_subssectors}")
            new_row = pd.DataFrame({"Sector_code": [parent_sector], "Parent_sector_code": ["other"], "emissions": [delta_emissions]})

            all_emissions_filtered = pd.concat([all_emissions_filtered, new_row], ignore_index=True)

        else:
            print(f"{sector} ok")



col_idx_subsector = all_emissions_filtered.columns.get_loc("Subsector1")

all_emissions_per_level = {}
for depth in range(1,levels+1):
    filtered = all_emissions_filtered[all_emissions_filtered.iloc[:, col_idx_subsector+depth:].isna().all(axis=1)]
    filtered = filtered[~filtered.iloc[:, col_idx_subsector+depth-1].isna()]

    if depth >= 2:
        previous_level = all_emissions_per_level[depth-1]
        aggregate_cols = ["Subsector" + str(i) for i in range(1, depth)]
        this_level_aggregated = filtered.groupby(aggregate_cols).sum()

    all_emissions_per_level[depth] = filtered

# Validate
aggregated_check = all_emissions_per_level[1][["Subsector1", "emissions"]]

for depth in range(2,levels+1):
    disaggregated = all_emissions_per_level[depth]
    disaggregated_check = disaggregated[["Subsector1", "emissions"]].groupby("Subsector1").sum().reset_index()

    for subsector in disaggregated_check["Subsector1"]:
        delta = disaggregated_check[disaggregated_check["Subsector1"] == subsector]["emissions"].sum().sum() - aggregated_check[aggregated_check["Subsector1"] == subsector]["emissions"].sum().sum()


st.write(all_emissions_per_level[2])

plot_data = all_emissions_per_level[3][["Subsector1","Subsector3", "emissions", "Sector_name"]]
chart = (
        alt.Chart(plot_data.reset_index())
        .mark_bar(color="steelblue")
        .encode(
            x=alt.X("emissions:Q", title="Emissions (t)"),
            color=alt.Color("Sector_name", title="Sector"),
        )
        .properties(
            width=400,
            height=300,
            title="Emissions per sector"
        )
    )

st.altair_chart(chart, width='stretch')

