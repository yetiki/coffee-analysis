import pandas as pd
import numpy as np
import plotly.graph_objects as go

"""

Assumptions made 

- there is a get_top3() in analyse-coffee.py 
returns a plain list of country name strings that exactly match 
the country_of_origin column values. Worth confirming that with 
whoever is writing that file.

- "Washed", "Natural", "Pulped-Natural", "Semi-Washed"  will be 
the data columns for processing type

"""

# ── Import from your analysis module ──────────────────────────────────────────
from analyse-coffee import get_top3  # returns a list of 3 country name strings
                                     # e.g. ["Ethiopia", "Colombia", "Kenya"]

# ── Config ────────────────────────────────────────────────────────────────────
CSV_PATH = "data/clean/coffee_ratings.csv"
OUTPUT_PATH = "output/chart1_scatter.png"

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)

# ── Aggregate by country ──────────────────────────────────────────────────────
# For each country we need: avg cupper_points, avg yum_score,
# total entry count, and % of entries that are washed processing.
agg = df.groupby("country_of_origin").agg(
    avg_cupper   = ("cupper_points", "mean"),
    avg_yum      = ("yum_score",     "mean"),
    entry_count  = ("cupper_points", "count"),
    washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
).reset_index()

agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]  # 0.0 – 1.0

# ── Get top 3 from analyse-coffee ─────────────────────────────────────────────
top3 = get_top3()  # ["Ethiopia", "Colombia", "Kenya"] - example

# ── Split into top-3 and the rest for layered plotting ────────────────────────
agg_rest = agg[~agg["country_of_origin"].isin(top3)]
agg_top3 = agg[agg["country_of_origin"].isin(top3)]

# ── Build figure ──────────────────────────────────────────────────────────────
fig = go.Figure()

# Layer 1 — all other countries (muted)
fig.add_trace(go.Scatter(
    x=agg_rest["avg_cupper"],
    y=agg_rest["avg_yum"],
    mode="markers",
    name="Other countries",
    marker=dict(
        size=agg_rest["entry_count"],
        sizemode="area",
        sizeref=2.0 * agg["entry_count"].max() / (40 ** 2),  # normalise bubble sizes
        sizemin=4,
        color=agg_rest["pct_washed"],
        colorscale="Teal",
        cmin=0, cmax=1,
        opacity=0.45,
        line=dict(width=0.5, color="white"),
    ),
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Avg cupper points: %{x:.2f}<br>"
        "Avg yum score: %{y:.3f}<br>"
        "Entries: %{customdata[1]}<br>"
        "% Washed: %{customdata[2]:.0%}"
        "<extra></extra>"
    ),
    customdata=list(zip(
        agg_rest["country_of_origin"],
        agg_rest["entry_count"],
        agg_rest["pct_washed"]
    ))
))

# Layer 2 — top 3 countries (highlighted)
fig.add_trace(go.Scatter(
    x=agg_top3["avg_cupper"],
    y=agg_top3["avg_yum"],
    mode="markers+text",
    name="Top 3 recommended",
    text=agg_top3["country_of_origin"],
    textposition="top center",
    textfont=dict(size=13, color="#1a1a1a", family="Arial Black"),
    marker=dict(
        size=agg_top3["entry_count"],
        sizemode="area",
        sizeref=2.0 * agg["entry_count"].max() / (40 ** 2),
        sizemin=4,
        color=agg_top3["pct_washed"],
        colorscale="Teal",
        cmin=0, cmax=1,
        opacity=1.0,
        line=dict(width=2.5, color="#ff6b35"),  # orange ring to make them pop
        showscale=True,
        colorbar=dict(
            title="% Washed<br>processing",
            tickformat=".0%",
            thickness=14,
            len=0.6,
        )
    ),
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Avg cupper points: %{x:.2f}<br>"
        "Avg yum score: %{y:.3f}<br>"
        "Entries: %{customdata[1]}<br>"
        "% Washed: %{customdata[2]:.0%}"
        "<extra></extra>"
    ),
    customdata=list(zip(
        agg_top3["country_of_origin"],
        agg_top3["entry_count"],
        agg_top3["pct_washed"]
    ))
))

# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text="Which country should we send our buyers to?<br>"
             "<sup>Bubble size = number of producers · Colour = % washed processing</sup>",
        font=dict(size=18, family="Arial"),
        x=0.5,
        xanchor="center"
    ),
    xaxis=dict(
        title="Average Cupper Points (0–10)",
        gridcolor="#ebebeb",
        zeroline=False,
    ),
    yaxis=dict(
        title="Average Yum Score (0–1)",
        gridcolor="#ebebeb",
        zeroline=False,
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.18,
        xanchor="center",
        x=0.5
    ),
    margin=dict(t=100, b=100, l=70, r=70),
    width=1000,
    height=680,
)

# ── Export ────────────────────────────────────────────────────────────────────
fig.write_image(OUTPUT_PATH, scale=2)  # scale=2 for high-res PNG
print(f"Chart 1 saved to {OUTPUT_PATH}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Processing Method Breakdown for Top 3 Countries (Stacked Bar)
# ══════════════════════════════════════════════════════════════════════════════
OUTPUT_PATH_2 = "output/chart2_processing.png"

# Processing method colour palette
# Washed is highlighted in the client's preferred teal; others are muted
PROCESSING_COLOURS = {
    "Washed":         "#2a9d8f",   # teal  — client's preferred method
    "Natural":        "#c9b99a",   # warm beige
    "Pulped-Natural": "#a07850",   # mid brown
    "Semi-Washed":    "#d4c5b0",   # light tan
}

# All four processing methods in a fixed order (Washed always on top)
PROCESSING_ORDER = ["Natural", "Pulped-Natural", "Semi-Washed", "Washed"]

# ── Filter to top 3 and count processing methods ──────────────────────────────
df_top3 = df[df["country_of_origin"].isin(top3)].copy()

# Normalise processing column to match our keys (strip whitespace, title case)
df_top3["processing"] = df_top3["processing"].str.strip().str.title()

processing_counts = (
    df_top3.groupby(["country_of_origin", "processing"])
    .size()
    .reset_index(name="count")
)

# Pivot so rows = countries, columns = processing methods
processing_pivot = processing_counts.pivot(
    index="country_of_origin",
    columns="processing",
    values="count"
).fillna(0).reindex(columns=PROCESSING_ORDER, fill_value=0)

# ── Build figure ──────────────────────────────────────────────────────────────
fig2 = go.Figure()

for method in PROCESSING_ORDER:
    fig2.add_trace(go.Bar(
        name=method,
        x=processing_pivot.index.tolist(),
        y=processing_pivot[method],
        marker_color=PROCESSING_COLOURS.get(method, "#cccccc"),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"{method}: " + "%{y} entries<extra></extra>"
        )
    ))

# ── Annotation: label the Washed % on each bar ────────────────────────────────
for country in processing_pivot.index:
    total = processing_pivot.loc[country].sum()
    washed = processing_pivot.loc[country].get("Washed", 0)
    pct = washed / total if total > 0 else 0
    fig2.add_annotation(
        x=country,
        y=total,
        text=f"{pct:.0%} washed",
        showarrow=False,
        yshift=10,
        font=dict(size=12, color="#2a9d8f", family="Arial Black"),
    )

# ── Layout ────────────────────────────────────────────────────────────────────
fig2.update_layout(
    barmode="stack",
    title=dict(
        text="Processing Method Breakdown — Top 3 Recommended Countries<br>"
             "<sup>Client preference: Washed processing (teal)</sup>",
        font=dict(size=18, family="Arial"),
        x=0.5,
        xanchor="center"
    ),
    xaxis=dict(
        title="Country",
        gridcolor="#ebebeb",
    ),
    yaxis=dict(
        title="Number of Entries",
        gridcolor="#ebebeb",
        zeroline=False,
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(
        title="Processing Method",
        orientation="h",
        yanchor="bottom",
        y=-0.22,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(t=100, b=110, l=70, r=70),
    width=900,
    height=600,
)

# ── Export ────────────────────────────────────────────────────────────────────
fig2.write_image(OUTPUT_PATH_2, scale=2)
print(f"Chart 2 saved to {OUTPUT_PATH_2}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Top 3 Country Profile Radar Chart
# ══════════════════════════════════════════════════════════════════════════════
OUTPUT_PATH_3 = "output/chart3_radar.png"

# Colour per country — distinct, accessible palette
COUNTRY_COLOURS = ["#2a9d8f", "#e76f51", "#e9c46a"]  # teal, coral, yellow

# ── Build per-country metrics for the top 3 ───────────────────────────────────
radar_rows = []

for country in top3:
    df_c = df[df["country_of_origin"] == country]
    radar_rows.append({
        "country":       country,
        "cupper_points": df_c["cupper_points"].mean(),
        "yum_score":     df_c["yum_score"].mean(),
        "pct_washed":    (df_c["processing"].str.strip().str.title() == "Washed").mean(),
        "entry_count":   len(df_c),
    })

radar_df = pd.DataFrame(radar_rows)

# ── Normalise all axes to 0–1 so the radar is visually balanced ───────────────
# cupper_points is 0–10 → divide by 10
# yum_score is already 0–1
# pct_washed is already 0–1
# entry_count → normalise against the max across the top 3
radar_df["norm_cupper"]  = radar_df["cupper_points"] / 10
radar_df["norm_yum"]     = radar_df["yum_score"]
radar_df["norm_washed"]  = radar_df["pct_washed"]
radar_df["norm_entries"] = radar_df["entry_count"] / radar_df["entry_count"].max()

# Axis labels shown on the radar
AXES = ["Cupper Points", "Yum Score", "% Washed", "Producer Volume"]
NORM_COLS = ["norm_cupper", "norm_yum", "norm_washed", "norm_entries"]

# ── Build figure ──────────────────────────────────────────────────────────────
fig3 = go.Figure()

for i, row in radar_df.iterrows():
    values = [row[col] for col in NORM_COLS]
    values_closed = values + [values[0]]   # close the polygon
    axes_closed   = AXES   + [AXES[0]]

    # Raw (un-normalised) values for the hover tooltip
    raw = [
        f"{row['cupper_points']:.2f} / 10",
        f"{row['yum_score']:.3f}",
        f"{row['pct_washed']:.0%}",
        f"{int(row['entry_count'])} entries",
    ]
    raw_closed = raw + [raw[0]]

    fig3.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=axes_closed,
        fill="toself",
        fillcolor=COUNTRY_COLOURS[list(radar_df.index).index(i)],
        opacity=0.25,
        line=dict(
            color=COUNTRY_COLOURS[list(radar_df.index).index(i)],
            width=2.5
        ),
        name=row["country"],
        hovertemplate=(
            "<b>" + row["country"] + "</b><br>"
            "%{theta}: %{customdata}<extra></extra>"
        ),
        customdata=raw_closed,
    ))

# ── Layout ────────────────────────────────────────────────────────────────────
fig3.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 1],
            tickvals=[0.25, 0.5, 0.75, 1.0],
            tickfont=dict(size=10, color="#888888"),
            gridcolor="#e0e0e0",
        ),
        angularaxis=dict(
            tickfont=dict(size=13, family="Arial", color="#1a1a1a"),
            gridcolor="#e0e0e0",
        ),
        bgcolor="white",
    ),
    title=dict(
        text="Top 3 Country Profiles — All Client Criteria at a Glance<br>"
             "<sup>All axes normalised to 0–1 · Hover for raw values</sup>",
        font=dict(size=18, family="Arial"),
        x=0.5,
        xanchor="center",
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.15,
        xanchor="center",
        x=0.5,
        font=dict(size=13),
    ),
    paper_bgcolor="white",
    margin=dict(t=100, b=100, l=80, r=80),
    width=750,
    height=700,
)

# ── Export ────────────────────────────────────────────────────────────────────
fig3.write_image(OUTPUT_PATH_3, scale=2)
print(f"Chart 3 saved to {OUTPUT_PATH_3}")