import pandas as pd
from scipy.stats import qmc
import streamlit as st

def sample(n_samples, path_ranges):
    ranges = pd.read_csv(path_ranges, sep=",")

    var_names = ranges["parameter"]

    lb = ranges["min"].to_list()
    ub = ranges["max"].to_list()

    sampler = qmc.LatinHypercube(d=len(ranges))
    sample = sampler.random(n=n_samples)

    sample_scaled = qmc.scale(sample, lb, ub)

    sample_scaled = pd.DataFrame(sample_scaled)
    sample_scaled.columns = var_names

    return sample_scaled