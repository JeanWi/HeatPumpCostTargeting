import streamlit as st

def manage_cash():
    if 'demand_profiles' not in st.session_state:
        st.session_state['demand_profiles'] = {}


def save_demand_profile(T_h, T_l, df):
    st.markdown("**Save heat demand profile**")
    profile_name = st.text_input("Profile name")
    if st.button("Save heat demand profile"):
        if profile_name not in st.session_state['demand_profiles']:
            st.session_state['demand_profiles'][profile_name] = {"T_h": T_h, "T_l":T_l, "profile": df[["datetime", "demand"]]}
            st.markdown(f"{profile_name} saved")
        else:
            st.markdown(f"{profile_name} already exists")
