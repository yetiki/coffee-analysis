import pandas as pd
import plotly.graph_objects as go


"""
Assumptions made — there is a get_top3() in analyse-coffee.py 
returns a plain list of country name strings that exactly match 
the country_of_origin column values. Worth confirming that with 
whoever is writing that file.

"""


# ── Import from your analysis module ──────────────────────────────────────────
from analyse_coffee import get_top3  # returns a list of 3 country name strings
                                     # e.g. ["Ethiopia", "Colombia", "Kenya"]

# ── Config ────────────────────────────────────────────────────────────────────
CSV_PATH = "data/coffee_clean.csv"
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