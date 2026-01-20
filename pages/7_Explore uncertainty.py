import streamlit as st
import altair as alt
import pandas as pd
import statsmodels.api as sm
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


import matplotlib.pyplot as plt

from src.cash_management import generate_sample

st.markdown("**Generate sample**")
exergetic_efficiency = st.number_input("Exergetic efficiency (%)", value=60.0, min_value=0.0, max_value=100.0,
                                       step=0.5) / 100
number_samples = st.number_input("Number of samples", value=100, min_value=1, max_value=10000,
                                 step=1)

if st.button("Generate"):
    generate_sample(number_samples, exergetic_efficiency)

if st.session_state['sample'] is not None:

    independent_vars = st.session_state['independent_vars']
    random_sample = st.session_state['sample']

    st.subheader("**Distribution of allowable investment costs**")
    chart = (
        alt.Chart(random_sample)
        .mark_bar()
        .encode(
            x=alt.X("allowable_costs:Q", bin=alt.Bin(step=5000)),
            y="count()"
        )
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Linear regression")
    dependent_var = "allowable_costs"

    random_sample["log_delta_T"] = np.log(random_sample["delta_T"] + 1e-9)

    # Replace delta_T with the logged version in the regression
    independent_vars_logged = [
        "log_delta_T" if var == "delta_T" else var
        for var in independent_vars
    ]

    X = random_sample[independent_vars_logged]

    X = sm.add_constant(X)
    y = random_sample[dependent_var]

    model = sm.OLS(y, X)
    results = model.fit()

    st.write(results.summary())

    st.subheader("Decision Tree")
    regression_or_classification = st.selectbox("Select for decision tree...", ["Regression", "Classification"])
    max_depth = st.number_input("Depth", value=2, min_value=1, max_value=5)
    train_size = st.number_input("Training sample size (% of samples)", value=70, min_value=1, max_value=100, step=1)/100

    if regression_or_classification == "Regression":
        regressor = DecisionTreeRegressor
        dependent_var = "allowable_costs"
        class_names = None
    elif regression_or_classification == "Classification":
        allowed_cost = st.number_input("Threshold investment cost of actual heat pump (EUR/kW)", value=2000, min_value=0, max_value=10000,)
        regressor = DecisionTreeClassifier
        dependent_var = "cost_category"
        bins = [-float('inf'), 0, allowed_cost, float('inf')]
        labels = ['negative', 'too expensive', 'profitable']
        random_sample['cost_category'] = pd.cut(random_sample['allowable_costs'], bins=bins, labels=labels)

    X = random_sample[independent_vars]
    y = random_sample[dependent_var]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1-train_size, random_state=42)
    clf = regressor(max_depth=max_depth)
    clf.fit(X_train, y_train)

    if regression_or_classification == "Classification":
        class_names = [str(c) for c in clf.classes_]
    else:
        class_names = None

    fig, ax = plt.subplots(figsize=(20, 8))
    plot_tree(
        clf,
        feature_names=independent_vars,
        class_names=class_names,
        filled=True,
        rounded=True,
        fontsize=10
    )
    st.pyplot(fig, use_container_width=True)

    st.subheader("Random Forest - Feature Importance")

    if regression_or_classification == "Regression":
        regressor_rf = RandomForestRegressor(n_estimators=1000, random_state=42)
    elif regression_or_classification == "Classification":
        regressor_rf = RandomForestClassifier(n_estimators=1000, random_state=42)

    rf = regressor_rf
    rf.fit(X_train, y_train)
    importances = rf.feature_importances_
    forest_importances = pd.Series(importances, index=X_train.columns)

    st.write(forest_importances.sort_values())



