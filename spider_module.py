import pandas as pd
import plotly.graph_objects as go
from shiny import module, ui, render, reactive
from shinywidgets import output_widget, render_widget

# ── Constants ─────────────────────────────────────────────────────────────────
AXES        = ["Aroma", "Flavor", "Body", "Uniformity"]
COLS        = ["aroma", "flavor", "body", "uniformity"]
COLOURS     = ["#2a9d8f", "#e76f51", "#e9c46a"]   # teal, coral, yellow — one per country
EMPTY_FIG   = go.Figure().update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    annotations=[dict(text="No data", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#aaaaaa"))]
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_top3_countries(data: pd.DataFrame) -> list[str]:
    """Return top 3 countries by composite score (mirrors new_get_top3 in app.py)."""
    if data.empty:
        return []

    agg = data.groupby("country_of_origin").agg(
        avg_cupper   = ("cupper_points", "mean"),
        avg_yum      = ("yum_score",     "mean"),
        entry_count  = ("cupper_points", "count"),
        washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
    ).reset_index()

    agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]

    for col in ["avg_cupper", "avg_yum", "pct_washed", "entry_count"]:
        col_min, col_max = agg[col].min(), agg[col].max()
        agg[f"norm_{col}"] = 0 if col_min == col_max else (agg[col] - col_min) / (col_max - col_min)

    agg["composite_score"] = (
        agg["norm_avg_cupper"] +
        agg["norm_avg_yum"]    +
        agg["norm_pct_washed"] +
        agg["norm_entry_count"]
    ) / 4

    return agg.nlargest(3, "composite_score")["country_of_origin"].tolist()


def get_top3_suppliers(data: pd.DataFrame, country: str) -> pd.DataFrame:
    """Return top 3 supplier rows for a given country, ranked by yum_score."""
    country_df = data[data["country_of_origin"] == country]
    return country_df.nlargest(3, "yum_score").reset_index(drop=True)


def make_radar(supplier_row: pd.Series, country: str, colour: str) -> go.Figure:
    """Build a single radar chart for one supplier."""
    values = [float(supplier_row[col]) / 10 for col in COLS]
    values_closed = values + [values[0]]
    axes_closed   = AXES  + [AXES[0]]

    raw_labels = [f"{supplier_row[col]:.2f} / 10" for col in COLS]
    raw_closed = raw_labels + [raw_labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=axes_closed,
        fill="toself",
        fillcolor=colour,
        opacity=0.25,
        line=dict(color=colour, width=2.5),
        name=country,
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        customdata=raw_closed,
    ))

    supplier_label = f"Yum: {supplier_row['yum_score']:.2f}  ·  Cupper: {supplier_row['cupper_points']:.1f}"

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0.25, 0.5, 0.75, 1.0],
                tickfont=dict(size=9, color="#888888"),
                gridcolor="#e0e0e0",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, family="Arial", color="#1a1a1a"),
                gridcolor="#e0e0e0",
            ),
            bgcolor="white",
        ),
        title=dict(
            text=supplier_label,
            font=dict(size=11, family="Arial", color="#444444"),
            x=0.5,
            xanchor="center",
        ),
        paper_bgcolor="white",
        margin=dict(t=60, b=20, l=40, r=40),
        height=280,
        showlegend=False,
    )
    return fig


# ── Module UI ─────────────────────────────────────────────────────────────────
@module.ui
def spider_ui():
    return ui.div(

        # Column headers (country names)
        ui.div(
            ui.output_text("country_label_0"),
            ui.output_text("country_label_1"),
            ui.output_text("country_label_2"),
            class_="spider-grid spider-header"
        ),

        # 3×3 radar chart grid
        ui.div(
            # Row 1 (supplier rank #1)
            output_widget("radar_0_0"),
            output_widget("radar_1_0"),
            output_widget("radar_2_0"),

            # Row 2 (supplier rank #2)
            output_widget("radar_0_1"),
            output_widget("radar_1_1"),
            output_widget("radar_2_1"),

            # Row 3 (supplier rank #3)
            output_widget("radar_0_2"),
            output_widget("radar_1_2"),
            output_widget("radar_2_2"),

            class_="spider-grid"
        ),

        # CSS injected directly
        ui.tags.style("""
            .spider-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 20px;
            }
            .spider-header {
                font-weight: bold;
                text-align: center;
                margin-bottom: 10px;
            }
        """)
    )


# ── Module Server ─────────────────────────────────────────────────────────────
@module.server
def spider_server(input, output, session, filtered_df):
    """
    filtered_df: a reactive expression passed in from app.py
    """

    @reactive.Calc
    def spider_data():
        d = filtered_df()
        countries = get_top3_countries(d)
        result = {}
        for country in countries:
            result[country] = get_top3_suppliers(d, country)
        return result

    # Factory functions — @output(id=...) must sit directly above @render.xx
    def make_chart_renderer(row_idx, col_idx):
        @output(id=f"radar_{row_idx}_{col_idx}")
        @render_widget
        def _render():
            data = spider_data()
            countries = list(data.keys())
            if row_idx >= len(countries):
                return EMPTY_FIG
            country   = countries[row_idx]
            suppliers = data[country]
            colour    = COLOURS[row_idx]
            if col_idx >= len(suppliers):
                return EMPTY_FIG
            return make_radar(suppliers.iloc[col_idx], country, colour)

    def make_label_renderer(row_idx):
        @output(id=f"country_label_{row_idx}")
        @render.text
        def _render():
            data = spider_data()
            countries = list(data.keys())
            if row_idx >= len(countries):
                return ""
            return f"#{row_idx + 1}  {countries[row_idx]}"

    # Call factories to register all 9 charts and 3 labels
    for r in range(3):
        make_label_renderer(r)
        for c in range(3):
            make_chart_renderer(r, c)
