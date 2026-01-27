import colorsys

import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from plotly import graph_objects as go


def lighten(color, amount=0.5):
    r, g, b = mcolors.to_rgb(color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = 1 - amount * (1 - l)
    return colorsys.hls_to_rgb(h, l, s)


def get_color(row, top_color_map):
    base = top_color_map[row["Subsector1"]]
    level = int(np.floor(row["aggregation_level"]))
    shade = min(0.85, 0.25 + 0.15 * level)

    col = lighten(base, shade)

    if row["is_missing"]:
        col = lighten(col, 0.15)  # grey-ish
    return col


def plot_bar(row, fig, trace_lookup):
    def rgb_tuple_to_plotly(rgb):
        if rgb is None or (isinstance(rgb, float) and np.isnan(rgb)):
            return "gray"
        else:
            return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    # st.write(row)
    fig.add_trace(go.Bar(
        x=[row["emissions"]], y=[row["aggregation_level"]],
        orientation='h',
        customdata=[[row["Sector_code"], row["aggregation_level"]]],
        marker=dict(
            color=rgb_tuple_to_plotly(row["color"]),
            line=dict(color='ghostwhite', width=1)
        ),
        hovertemplate=(
            "Sector: " + str(row["Sector_name"]) + "<br>"
            "Emissions: %{x:,.0f}<extra></extra>"
        ),
    ))

    trace_lookup.append({
        "Sector_code": row["Sector_code"],
        "aggregation_level": row["aggregation_level"],
        "Parent_sector_code": row["Parent_sector_code"],
    })


def add_missing_emissions(total_emissions, child_sectors, aggregation_level, sector_name):
    missing_emissions = total_emissions - child_sectors["emissions"].sum()
    if missing_emissions > 0.01:
        child_sectors = pd.concat([
            child_sectors,
            pd.DataFrame([{
                "Sector_name": sector_name,
                "aggregation_level": aggregation_level,
                "emissions": missing_emissions,
                "color": (1,1,1),
            }])
        ], ignore_index=True)
    return child_sectors


def lighten_color(rgb, fraction):
    """
    Lighten an RGB tuple (0-1 or 0-255) by fraction (0 = original, 1 = white)
    Returns Plotly-friendly 'rgb(r,g,b)' string
    """
    if rgb is None or (isinstance(rgb, float) and np.isnan(rgb)):
        return "gray"

    r, g, b = rgb

    # convert 0-255 -> 0-1 if needed
    if max(r, g, b) > 1.0:
        r, g, b = r/255, g/255, b/255

    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # increase lightness toward white
    l = l + fraction*(1 - l)
    l = min(1.0, l)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (r,g,b)


def set_colors(df_level, base_color):
    """
    Assign shades of the base_color across the dataframe.
    Top row = darkest, last row = lightest.
    """
    df = df_level.copy()
    n = len(df)
    if n == 0:
        return df

    shades = np.linspace(0.2, 0.9, n)  # fraction of lightening (0=dark, 0.5=lighter)
    df["color"] = [lighten_color(base_color, f) for f in shades]
    return df


def plot_sector_recursive(row, df_plot, fig, current_level, max_level, trace_lookup):

    next_level = current_level + 1
    if current_level > max_level:
        return

    plot_bar(row, fig, trace_lookup)
    total_emissions = row["emissions"]
    df_level_next_level = df_plot[df_plot["Parent_sector_code"] == row["Sector_code"]]
    df_level_next_level = set_colors(df_level_next_level, row["color"])
    df_level_next_level = add_missing_emissions(total_emissions, df_level_next_level, next_level, row["Sector_code"])
    for _, row_next_level in df_level_next_level[df_level_next_level["aggregation_level"] == next_level].iterrows():
        plot_sector_recursive(
            row=row_next_level,
            df_plot=df_plot,
            fig=fig,
            current_level=next_level,
            max_level=max_level,
            trace_lookup = trace_lookup
        )
