import streamlit as st

def manage_cash():
    if 'demand_profiles' not in st.session_state:
        st.session_state['demand_profiles'] = {}
