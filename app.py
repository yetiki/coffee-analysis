from shiny import App, ui, render, reactive, run_app
from shinywidgets import output_widget, render_widget
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

# ── Global Setup & Data Loading ───────────────────────────────────────────────
# Load main dataset
df = pd.read_csv("data/clean/coffee_ratings.csv")


# ── Data Preprocessing & Normalisation ────────────────────────────────────────
# Handle column name mismatches from different data sources
if 'processing_method' in df.columns and 'processing' not in df.columns:
    df = df.rename(columns={'processing_method': 'processing'})

# Ensure we have a quality metric (0-10 scale)
if 'cupper_points' not in df.columns:
    # Use 'flavor' as a proxy for the cupper points if total score isn't there
    df['cupper_points'] = df['flavor'] if 'flavor' in df.columns else np.nan

# Ensure we have a "yum" metric (0-1 scale)
if 'yum_score' not in df.columns:
    # Create a synthetic score from available sensory columns
    sensory_cols = [c for c in ['aroma', 'flavor', 'body', 'uniformity'] if c in df.columns]
    if sensory_cols:
        df['yum_score'] = df[sensory_cols].mean(axis=1) / 10
    else:
        df['yum_score'] = 0.5 # default fallback

# Load map data globally to avoid re-fetching
WORLD_URL = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(WORLD_URL)

# ── Helper Functions (Adapted from visualise-coffee.py) ───────────────────────
def get_top_countries(data, n=3):
    """Dynamically determine top n countries by average cupper score."""
    if data.empty: return []
    # Only consider countries with > 1 entry to avoid outliers
    counts = data['country_of_origin'].value_counts()
    valid_countries = counts[counts > 1].index
    
    subset = data[data['country_of_origin'].isin(valid_countries)]
    if subset.empty: subset = data 
    
    agg = subset.groupby("country_of_origin")["cupper_points"].mean()
    return agg.sort_values(ascending=False).head(n).index.tolist()

# ── UI Definition ─────────────────────────────────────────────────────────────
app_ui = ui.page_fluid(
    ui.h2("Coffee Analysis Dashboard"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Filters"),
            ui.input_selectize(
                "countries", "Country of Origin",
                choices=sorted(df["country_of_origin"].unique().tolist()),
                multiple=True
            ),
            ui.input_selectize(
                "processing", "Processing Method",
                choices=sorted(df["processing"].fillna("Unknown").astype(str).unique().tolist()),
                multiple=True
            ),
            ui.input_slider(
                "bags_range", "Number of Bags",
                min=int(df["number_of_bags"].min()),
                max=int(df["number_of_bags"].max()),
                value=[int(df["number_of_bags"].min()), int(df["number_of_bags"].max())]
            ),
            ui.input_slider(
                "weight_range", "Bag Weight (kg)",
                min=float(df["bag_weight"].min()),
                max=float(df["bag_weight"].max()),
                value=[float(df["bag_weight"].min()), float(df["bag_weight"].max())]
            ),
            bg="#f8f9fa"
        ),
        
        # 1. Data Table
        ui.card(
            ui.card_header("Dataset Explorer"),
            ui.output_data_frame("table"),
            height="300px"
        ),
        
        # 2. Key Plots Row
        ui.layout_column_wrap(
            ui.card(output_widget("chart_scatter")),
            ui.card(output_widget("chart_bar")),
            ui.card(output_widget("chart_radar")),
            width=1/3
        ),
        
        # 3. Map
        ui.card(
            ui.card_header("Global Supplier Distribution"),
            output_widget("map_plot"),
            height="500px"
        )
    )
)

# ── Server Logic ──────────────────────────────────────────────────────────────
def server(input, output, session):
    
    @reactive.Calc
    def filtered_df():
        d = df.copy()
        if input.countries():
            d = d[d["country_of_origin"].isin(input.countries())]
        if input.processing():
             d = d[d["processing"].fillna("Unknown").isin(input.processing())]
        
        # Apply numeric range filters
        d = d[(d["number_of_bags"] >= input.bags_range()[0]) & (d["number_of_bags"] <= input.bags_range()[1])]
        d = d[(d["bag_weight"] >= input.weight_range()[0]) & (d["bag_weight"] <= input.weight_range()[1])]
        return d

    @render.data_frame
    def table():
        return render.DataGrid(filtered_df(), selection_mode="rows")

    # --- Chart 1: Scatter (Bubble) ---
    @render_widget
    def chart_scatter():
        d = filtered_df()
        if d.empty: return go.Figure()

        # Aggregation logic adapted from visualise-coffee.py
        agg = d.groupby("country_of_origin").agg(
            avg_cupper   = ("cupper_points", "mean"),
            avg_yum      = ("yum_score",     "mean"),
            entry_count  = ("cupper_points", "count"),
            washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
        ).reset_index()
        agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]

        top3 = get_top_countries(d)
        agg_rest = agg[~agg["country_of_origin"].isin(top3)]
        agg_top3 = agg[agg["country_of_origin"].isin(top3)]

        fig = go.Figure()
        
        # Layer 1: Rest
        fig.add_trace(go.Scatter(
            x=agg_rest["avg_cupper"], y=agg_rest["avg_yum"], mode="markers",
            name="Other",
            marker=dict(size=agg_rest["entry_count"], sizemode="area", sizeref=2.*agg["entry_count"].max()/(40**2), sizemin=4,
                        color=agg_rest["pct_washed"], colorscale="Teal", opacity=0.45),
            text=agg_rest["country_of_origin"]
        ))
        
        # Layer 2: Top 3
        fig.add_trace(go.Scatter(
            x=agg_top3["avg_cupper"], y=agg_top3["avg_yum"], mode="markers+text",
            name="Top Recommended", text=agg_top3["country_of_origin"], textposition="top center",
            marker=dict(size=agg_top3["entry_count"], sizemode="area", sizeref=2.*agg["entry_count"].max()/(40**2), sizemin=4,
                        color=agg_top3["pct_washed"], colorscale="Teal", line=dict(width=2, color="#ff6b35"))
        ))
        
        fig.update_layout(title="Performance vs Flavour", margin=dict(l=20, r=20, t=40, b=20), height=300)
        return fig

    # --- Chart 2: Stacked Bar ---
    @render_widget
    def chart_bar():
        d = filtered_df()
        top3 = get_top_countries(d)
        if not top3: return go.Figure()
        
        d_top3 = d[d["country_of_origin"].isin(top3)].copy()
        d_top3["processing"] = d_top3["processing"].str.strip().str.title().fillna("Unknown")
        
        counts = d_top3.groupby(["country_of_origin", "processing"]).size().reset_index(name="count")
        
        # Pivot logic
        methods = sorted(counts["processing"].unique())
        pivot = counts.pivot(index="country_of_origin", columns="processing", values="count").fillna(0)
        
        fig = go.Figure()
        for method in methods:
            fig.add_trace(go.Bar(name=method, x=pivot.index, y=pivot[method]))
            
        fig.update_layout(barmode="stack", title="Processing Methods (Top 3)", margin=dict(l=20, r=20, t=40, b=20), height=300)
        return fig

    # --- Chart 3: Radar ---
    @render_widget
    def chart_radar():
        d = filtered_df()
        country_names = get_top_countries(d)
        if not country_names: return go.Figure()

        fig = go.Figure()
        
        # Normalize metrics for radar
        metrics = []
        for country in country_names:
            sub = d[d["country_of_origin"] == country]
            metrics.append({
                "country": country,
                "Quality": sub["cupper_points"].mean() / 10,  # Norm 0-1
                "Yum": sub["yum_score"].mean(),
                "Washed": (sub["processing"].str.lower() == "washed").mean(),
                "Volume": len(sub)
            })
        
        # Prepare for plotting
        max_vol = max([m["Volume"] for m in metrics]) if metrics else 1
        
        for m in metrics:
            r_vals = [m["Quality"], m["Yum"], m["Washed"], m["Volume"]/max_vol]
            r_vals += [r_vals[0]] # Close loop
            theta = ["Quality", "Yum", "% Washed", "Volume", "Quality"]
            
            fig.add_trace(go.Scatterpolar(
                r=r_vals, theta=theta, fill="toself", name=m["country"]
            ))

        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
                          title="Profile Comparison", margin=dict(l=40, r=40, t=40, b=20), height=300)
        return fig

    # --- Map Plot ---
    @render_widget
    def map_plot():
        d = filtered_df()
        if d.empty: return go.Figure()
        
        counts = d['country_of_origin'].value_counts().reset_index()
        counts.columns = ['country_name', 'rating_count']
        
        fig = go.Figure(data=go.Choropleth(
            locations=counts['country_name'],
            z=counts['rating_count'],
            locationmode='country names', # Uses Plotly's built-in country geometry
            colorscale='OrRd',
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_title="Suppliers",
            text=counts['country_name']
        ))

        fig.update_layout(
            title_text=f"Supplier Locations (Total: {len(d)})",
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth'
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        return fig

app = App(app_ui, server)

if __name__ == "__main__":
    run_app(app, launch_browser=True)