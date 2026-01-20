import streamlit as st
import numpy as np
import altair as alt
import pandas as pd
import pyomo.environ as pyo
import io
import contextlib

from src.price_profile_generation import generate_electricity_price_profile, load_electricity_price_profile, fit_electricty_price_trends
from src.calculate_allowable_investment_cost import calculate_allowable_investment_cost
from src.carnot_hp_calculations import calculate_cop, calculate_annuity_factor

def extract_time_series(model, time_set):
    data = {}

    # Loop over Vars and Params
    for comp in model.component_objects((pyo.Var, pyo.Param), active=True):
        name = comp.name

        # Scalar → skip
        if not comp.is_indexed():
            continue

        # Check whether time_set is part of the index
        index_sets = comp.index_set().subsets()
        if time_set not in index_sets:
            continue

        # Initialize column
        data[name] = []

        for t in time_set:
            val = comp[t]
            data[name].append(pyo.value(val) if val is not None else None)

    return pd.DataFrame(data, index=list(time_set))

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Process specifications**")
    exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0,
                                           step=0.5) / 100
    T_l = st.number_input("Temperature of heat source in Celsius", value=30.0, min_value=-20.0, max_value=150.0,
                          step=0.5)
    T_h = st.number_input("Temperature of heat sink in Celsius", value=90.0, min_value=0.0, max_value=250.0, step=0.5)

    st.markdown("**Profile specifications**")
    weekly_factor = st.number_input("Weekly factor", value=1.0, min_value=0.0, max_value=1.3,)
    hourly_factor = st.number_input("Hourly factor", value=1.0, min_value=0.0, max_value=1.3,)
    overall_factor = st.number_input("Overall factor", value=1.0, min_value=0.0, max_value=3.0,)
    rho = st.number_input("Correlation between heat demand and electricity price", value=0.0, min_value=-1.0, max_value=1.0,)
    variation_heat_dem = st.number_input("Fluctuation of heat demand (1=high, 0=low)", value=0.0, min_value=0.0, max_value=1.0)



with col2:
    st.markdown("**Economic assumptions**")

    p_el = st.number_input("Average cost of electricity for heat pump (EUR/MW)", value=150, min_value=0, max_value=300)
    p_th = st.number_input("Cost of alternative heat provision (EUR/MWth)", value=50, min_value = 0, max_value = 2000)

    lifetime = st.number_input("Lifetime of heat pump", value=15, min_value=0, max_value=100)
    interest_rate = st.number_input("Interest rate", value=5.0, min_value=0.1, max_value=20.0) / 100


scaling = {
    "trend": 0,
    "weekly_factor": weekly_factor,
    "hourly_factor": hourly_factor,
    "overall_factor": overall_factor
}

ctr_sel = "Germany"
selected_years = 2023
p_original = load_electricity_price_profile(ctr_sel)
p_predicted, params = fit_electricty_price_trends(p_original, selected_years)
p_gen = generate_electricity_price_profile(params, p_el, scaling, selected_years)

# Generate random heating demand
noise = np.random.rand(len(p_gen["p"]))
heat_demand = (rho * p_gen["p"] + np.sqrt(1 - rho ** 2) * noise)
# Shift to zero mean
heat_demand = (heat_demand - heat_demand.min()) / (heat_demand.max() - heat_demand.min()) * variation_heat_dem
max_heat_demand = heat_demand.max()
heat_demand = heat_demand + (1-max_heat_demand)
st.write(heat_demand.max())
st.write(heat_demand.mean())
p_gen["heat_demand"] = heat_demand
allowable_cost = calculate_allowable_investment_cost(
    p_gen["heat_demand"],
    p_gen["p"] / 1000,
    p_th / 1000,
    T_l,
    T_h,
    exergetic_efficiency,
    interest_rate,
    lifetime
)

st.subheader("**Demand and price profiles**")
min_time = p_gen.index.min()
max_time = p_gen.index.max()

start, end = st.slider(
    "Select time range",
    min_value=min_time.to_pydatetime(),
    max_value=max_time.to_pydatetime(),
    value=(min_time.to_pydatetime(), max_time.to_pydatetime()),
)

p_gen_plot = p_gen["p"]
p_gen_plot.index.name = None
p_gen_plot.name = "Generic price profile"
p_gen_plot = p_gen_plot.to_frame(name="p").assign(source=p_gen_plot.name)

demand = p_gen["heat_demand"]*100
demand.index.name = None
demand.name = "Heat demand (between 0-100)"
demand  = demand.to_frame(name="p").assign(source=demand.name)

p_plot = pd.concat([demand, p_gen_plot])

p_plot_sel = p_plot[(p_plot.index >= start) & (p_plot.index <= end)]

chart = (
    alt.Chart(p_plot_sel.reset_index())
    .mark_line()
    .encode(
        x=alt.X("index:T", title="Time"),
        y=alt.Y("p:Q", title="Electricity Price (EUR/MWh)"),
        color=alt.Color(
            "source:N",
            title="Price profile",
            scale=alt.Scale(
                range=["crimson", "steelblue"]  # choose any colors
            )
        )
    )
    .interactive()
)

st.altair_chart(chart, width='stretch')

st.subheader("**Results**")

st.write(f"Allowable investment costs: {round(allowable_cost,2)} EUR/kW")


st.subheader("**Optimizing supply system**")

flexibility_model = st.selectbox("Select flexibility model", options=["Heat storage", "Demand side response"])



if st.button("Solve"):
    # parameters
    cop = calculate_cop(T_l + 273, T_h + 273, exergetic_efficiency)
    l = 10
    # time_steps = 100
    time_steps = len(p_gen["p"])-1

    m = pyo.ConcreteModel()

    # sets
    m.set_t = pyo.RangeSet(0, time_steps)

    # parameters
    m.par_demand = pyo.Param(m.set_t, initialize={t: p_gen["heat_demand"].iloc[t] for t in m.set_t})
    m.par_p_el = pyo.Param(m.set_t, initialize={t: p_gen["p"].iloc[t] / 1000 for t in m.set_t})  # EUR/kWh
    m.par_cost_alternative = pyo.Param(initialize=p_gen["heat_demand"].sum() * p_th / 1000)  # EUR/kWh
    m.par_annuity_factor = pyo.Param(initialize=calculate_annuity_factor(interest_rate, lifetime))

    # dsr parameters
    m.par_l = pyo.Param(within=pyo.NonNegativeIntegers, initialize=l)
    par_demand_upper_plus = max(p_gen["heat_demand"])
    par_demand_upper_minus = max(p_gen["heat_demand"])

    # variables
    m.var_hp_capacity = pyo.Param(initialize=1/cop)
    m.var_input = pyo.Var(m.set_t, within=pyo.NonNegativeReals)
    m.var_output = pyo.Var(m.set_t, within=pyo.NonNegativeReals)
    m.var_allowable_cost = pyo.Var(within=pyo.NonNegativeReals)
    m.var_electricity_cost = pyo.Var(within=pyo.NonNegativeReals)
    m.var_delta = pyo.Var(m.set_t, within=pyo.Binary)

    # dsr variables
    m.var_demand_flex = pyo.Var(m.set_t, within=pyo.NonNegativeReals)
    m.var_demand_d_plus = pyo.Var(m.set_t, within=pyo.NonNegativeReals, bounds=[0, par_demand_upper_plus])
    m.var_demand_d_minus = pyo.Var(m.set_t, within=pyo.NonNegativeReals, bounds=[0, par_demand_upper_minus])
    m.var_e = pyo.Var(m.set_t, within=pyo.NonNegativeReals)

    # technology constraints
    def init_input_output(const, t):
        return m.var_output[t] <= cop * m.var_input[t]
    m.con_input_output = pyo.Constraint(m.set_t, rule=init_input_output)

    def init_capacity(const, t):
        return m.var_input[t] <= m.var_hp_capacity
    m.con_capacity = pyo.Constraint(m.set_t, rule=init_capacity)

    # demand response constraints
    # 55
    def init_dr55(const, t):
        return m.var_demand_flex[t] == m.par_demand[t] + m.var_demand_d_plus[t] - m.var_demand_d_minus[t]
    m.con_dr55 = pyo.Constraint(m.set_t, rule=init_dr55)

    # 56
    def init_dr56(const, t):
        if t >=1:
            return m.var_e[t] == m.var_e[t-1] + m.var_demand_d_minus[t] - m.var_demand_d_plus[t]
        else:
            return m.var_e[t] == m.var_e[max(m.set_t)] + m.var_demand_d_minus[t] - m.var_demand_d_plus[t]
    m.con_dr56 = pyo.Constraint(m.set_t, rule=init_dr56)


    # 57
    def init_dr57(const, t):
        return m.var_e[t] <= sum(m.var_demand_d_plus[t + l]
                                 if t + l <= max(m.set_t)
                                 else m.var_demand_d_plus[l - 1]
                                 for l in range(1, int(m.par_l) + 1))


    m.con_dr57 = pyo.Constraint(m.set_t, rule=init_dr57)

    # 58
    def init_dr58(const, t):
            return m.var_e[t] <= sum(m.var_demand_d_minus[t-l]
                                     if t-l >=0
                                     else m.var_demand_d_minus[max(m.set_t)-l+1]
                                     for l in range(0, int(m.par_l)))
    m.con_dr58 = pyo.Constraint(m.set_t, rule=init_dr58)


    # 61
    def init_dr61(const, t):
        return m.var_demand_d_plus[t] <= par_demand_upper_plus * m.var_delta[t]
    m.con_dr61 = pyo.Constraint(m.set_t, rule=init_dr61)

    # 62
    def init_dr62(const, t):
        return m.var_demand_d_minus[t] <= par_demand_upper_minus * (1 - m.var_delta[t])
    m.con_dr62 = pyo.Constraint(m.set_t, rule=init_dr62)

    def init_energybalance(const, t):
        return m.var_output[t] >= m.var_demand_flex[t]
    m.con_energybalance = pyo.Constraint(m.set_t, rule=init_energybalance)

    def init_electricity_cost(m):
        return m.var_electricity_cost == sum(m.par_p_el[t] * m.var_input[t] for t in m.set_t)
    m.con_electricity_cost = pyo.Constraint(rule=init_electricity_cost)

    def init_cost(m):
        return (m.par_cost_alternative - m.var_electricity_cost) / m.var_hp_capacity * m.par_annuity_factor == m.var_allowable_cost
    m.con_cost = pyo.Constraint(rule=init_cost)

    m.obj_cost = pyo.Objective(expr= - m.var_allowable_cost)

    solver = pyo.SolverFactory("gurobi")

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        results = solver.solve(m, tee=True)

    solver_log = buffer.getvalue()

    st.code(solver_log, language="text")


    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        m.pprint()

    st.text(buffer.getvalue())

    df = extract_time_series(m, m.set_t)
    df.to_csv('data/model_results.csv')