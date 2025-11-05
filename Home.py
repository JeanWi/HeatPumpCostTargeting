import streamlit as st
from src import manage_cash

manage_cash()

st.set_page_config(
    page_title="Home",
)

st.markdown("Enjoy playing around")