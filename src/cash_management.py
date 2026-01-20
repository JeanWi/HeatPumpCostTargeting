import streamlit as st
import numpy as np

from src.sampling import sample
from src.price_profile_generation import generate_electricity_price_profile, load_electricity_price_profile, fit_electricty_price_trends
from src.calculate_allowable_investment_cost import calculate_allowable_investment_cost

def manage_cash():
    if 'demand_profiles' not in st.session_state:
        st.session_state['demand_profiles'] = {}
    if 'sample' not in st.session_state:
        st.session_state['sample'] = None
        st.session_state['independent_vars'] = None


def save_demand_profile(T_h, T_l, df):
    st.markdown("**Save heat demand profile**")
    profile_name = st.text_input("Profile name")
    if st.button("Save heat demand profile"):
        if profile_name not in st.session_state['demand_profiles']:
            st.session_state['demand_profiles'][profile_name] = {"T_h": T_h, "T_l":T_l, "profile": df[["datetime", "demand"]]}
            st.markdown(f"{profile_name} saved")
        else:
            st.markdown(f"{profile_name} already exists")


def generate_sample(n, exergetic_efficiency):
    def compute_allowable_costs(row):
        avg_el = row["p_el"]
        scaling = {
            "trend": 0,
            "weekly_factor": row["weekly_factor"],
            "hourly_factor": row["hourly_factor"],
            "overall_factor": row["overall_factor"]
        }

        p_gen = generate_electricity_price_profile(params, avg_el, scaling, selected_years)

        # Generate random heating demand
        rho = row["correl_el_demand"]
        noise = np.random.rand(len(p_gen["p"]))
        heat_demand = rho * p_gen["p"] + np.sqrt(1 - rho ** 2) * noise
        p_gen["heat_demand"] = (heat_demand - heat_demand.min()) / (heat_demand.max() - heat_demand.min())

        T_l = row["T_l"]
        T_h = T_l + row["delta_T"]
        p_th = row["p_ng"]
        interest_rate = 0.08
        lifetime = 15

        return calculate_allowable_investment_cost(
            p_gen["heat_demand"],
            p_gen["p"] / 1000,
            p_th / 1000,
            T_l,
            T_h,
            exergetic_efficiency,
            interest_rate,
            lifetime
        )


    ctr_sel = "Germany"
    selected_years = 2024
    p_original = load_electricity_price_profile(ctr_sel)

    p_predicted, params = fit_electricty_price_trends(p_original, selected_years)

    random_sample = sample(n, "data/DataRanges.csv")
    st.session_state['independent_vars'] = random_sample.columns.to_list()

    random_sample["allowable_costs"] = random_sample.apply(compute_allowable_costs, axis=1)

    st.session_state['sample'] = random_sample

