import pandas as pd


def process_price_data(path:str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0).apply(pd.to_numeric, errors='coerce')
    df = df.dropna(axis=1, how='all')
    return df.dropna(axis=0, how='any')


def get_relative_prices() -> pd.DataFrame:
    p_el = process_price_data("data/industrial_el_prices.csv")
    p_th = process_price_data("data/industrial_gas_prices.csv")
    p_rel = p_el.divide(p_th)
    return p_rel.dropna(axis=0, how='any')
