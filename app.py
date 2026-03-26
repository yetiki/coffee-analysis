from shiny import App, ui, render, reactive, run_app
from shinywidgets import output_widget, render_widget
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

#from analyse_coffee import get_top3 this version is hard coded to using the CSV

# ── Global Setup & Data Loading ───────────────────────────────────────────────
# Load main dataset
print("Loading dataset from:", "data/results/coffee_ratings_yscore.csv")
df = pd.read_csv("data/results/coffee_ratings_yscore.csv")
#print column names
df.columns.tolist()
# ['species', 'country_of_origin', 'number_of_bags', 'bag_weight', 'processing', 'aroma', 'flavor', 'body', 'uniformity', 'cupper_points', 'yum_score']

#print the catagories in country of origin and processing
# print("Countries of Origin:", df["country_of_origin"].unique())
# print("Processing Methods:", df["processing"].unique())

# this should be using the get_top3 function from visualise-coffee.py
# but that first needs to be refactored to work dymanically with filtered data.
def new_get_top3(data: pd.DataFrame):
    """Determine the top 3 countries based on a composite score."""
    if data.empty:
        return []

    agg = data.groupby("country_of_origin").agg(
        avg_cupper   = ("cupper_points", "mean"),
        avg_yum      = ("yum_score",     "mean"),
        entry_count  = ("cupper_points", "count"),
        washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
    ).reset_index()

    agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]

    # Normalize each criterion to 0-1 then combine into a composite score
    for col in ["avg_cupper", "avg_yum", "pct_washed", "entry_count"]:
        col_min, col_max = agg[col].min(), agg[col].max()
        agg[f"norm_{col}"] = (agg[col] - col_min) / (col_max - col_min)

    agg["composite_score"] = (
        agg["norm_avg_cupper"] +
        agg["norm_avg_yum"] +
        agg["norm_pct_washed"] +
        agg["norm_entry_count"]
    ) / 4

    top3 = agg.nlargest(3, "composite_score")["country_of_origin"].tolist()
    return top3

# Load map data globally to avoid re-fetching
world = gpd.read_file("https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")

# ── UI Definition ─────────────────────────────────────────────────────────────
# The UI is structured with a sidebar for filters and a main area for visualizations.
app_ui = ui.page_fluid(
    ui.h2("Coffee Analysis Dashboard"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Filters"),
            ui.input_selectize( # add a box to select multiple countries of origin, from a drop down list of the unique values in the country_of_origin column
                "countries", "Country of Origin",
                choices=sorted(df["country_of_origin"].unique().tolist()),
                multiple=True
            ), 
            ui.input_selectize( # add a box to select species
                "species", "Species",
                choices=sorted(df["species"].unique().tolist()),
                multiple=True
            ),
            ui.input_selectize( # add a box to select processing method, but first fill any missing values with "Unknown" and strip whitespace and title case the options
                "processing", "Processing Method",
                choices=sorted(df["processing"].fillna("Unknown").astype(str).unique().tolist()),
                multiple=True
            ),
            ui.input_slider( # add a slider to filter by cupper points, use the min and max values from the dataset
                "cupper_points_range", "Cupper Points",
                min=float(df["cupper_points"].min()),
                max=float(df["cupper_points"].max()),
                value=[float(df["cupper_points"].min()), float(df["cupper_points"].max())]
            ),
            ui.input_slider( # add a slider to filter by yum score
                "yum_score_range", "Yum Score",
                min=float(df["yum_score"].min()),
                max=float(df["yum_score"].max()),
                value=[float(df["yum_score"].min()), float(df["yum_score"].max())]
            ),
            ui.input_slider( # add a slider to filter by bag weight
                "weight_range", "Bag Weight (kg)",
                min=float(df["bag_weight"].min()),
                max=float(df["bag_weight"].max()),
                value=[float(df["bag_weight"].min()), float(df["bag_weight"].max())]
            ),
            bg="#f8f9fa"
        ),
        
        # Data Table - at the top of the main area
        # This will show the filtered dataset
        # it should by default be sorted by yum score in descending order, I think....
        # the user should also che able to sort by any column by clicking on the column header
        ui.card(
            ui.card_header("Dataset Explorer"),
            ui.output_data_frame("table"),
            height="300px"
        ),
        
        # scatter plot
        ui.card(output_widget("chart_scatter")),

        # bar chart and radar chart should be side by side below the scatter plot
        ui.layout_column_wrap(
            ui.card(output_widget("chart_bar")),
            ui.card(output_widget("chart_radar")),
            width="1/2"
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
        if input.countries():  # Call the method with parentheses
            d = d[d["country_of_origin"].isin(input.countries())]
        if input.species():
            d = d[d["species"].isin(input.species())]
        if input.processing():  # Call the method with parentheses
            d = d[d["processing"].fillna("Unknown").isin(input.processing())]
        
        # Apply numeric range filters
        d = d[(d["cupper_points"] >= input.cupper_points_range()[0]) & (d["cupper_points"] <= input.cupper_points_range()[1])]
        d = d[(d["yum_score"] >= input.yum_score_range()[0]) & (d["yum_score"] <= input.yum_score_range()[1])]
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

        top3 = new_get_top3(d)
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
        
        fig.update_layout(title="Performance vs Flavour", margin=dict(l=20, r=20, t=40, b=20), height=400)
        return fig

    # --- Chart 2: Stacked Bar ---
    @render_widget
    def chart_bar():
        d = filtered_df()
        top3 = new_get_top3(d)
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
        country_names = new_get_top3(d)
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
                "Washed": (sub["processing"].astype(str).str.lower() == "washed").mean(),
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

# This conditional block checks if the script is executed directly.
# If it is, it runs the Shiny app, launching it in a browser.
if __name__ == "__main__":
    run_app(app, launch_browser=True)
