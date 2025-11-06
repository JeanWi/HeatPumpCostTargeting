import streamlit as st
from src import manage_cash

manage_cash()

st.set_page_config(
    page_title="Home",
)


st.markdown("**Relative electricity prices**  \n"
            "Takes a carnot heat pump with an exergetic efficiency and shows the source/sink temperatures"
            "for which the respective relative electricity price (i.e. electricity price/ heat production cost of "
            "alternative) a heat pump is profitable (operational costs only)"
            )
st.markdown("**Allowable investment cost (general)**  \n"
            "Takes a carnot heat pump with an exergetic efficiency for given the source/sink temperatures, "
            "operational hours, electricity prices, interest rate, lifetime and cost of alternative heat generation"
            "and calculates the maximal allowable heat pump investment cost for the respective application."
            )
st.markdown("**Generate process heat demand profile**  \n"
            "Allows to generate an annual heat demand profile for batch and continuous processes to be used to calculate"
            "the allowable investment costs for a process operation over a full year. This can be done in 'Allowable "
            "investment cost (specific case)'"
            )
st.markdown("**Allowable investment cost (specific case)**  \n"
            "Calculates the allowable maximal investment cost for each of the processes defined in the section before."
            "Different electricity price assumptions can be taken."
            )