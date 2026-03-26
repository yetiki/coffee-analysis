from shiny import App, ui, render, reactive, run_app
from shinywidgets import output_widget, render_widget
from spider_module import spider_ui, spider_server
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np


def new_get_top3(coffee_df: pd.DataFrame) -> list[str]:
    """
    Determine the top 3 countries based on a composite score.
    The composite score is calculated by normalizing and averaging the following criteria:
    - Average cupper points (quality)
    - Average yum score (flavour)
    - Percentage of washed processing (consistency)
    - Number of entries (volume)

    Parameters:
    -----------
    coffee_df : pd.DataFrame
        The DataFrame containing coffee ratings data.

    Returns:
    --------
    list[str]
        A list of the top 3 country names based on the composite score.
    """
    if coffee_df.empty:
        return []

    aggregated_scores: pd.DataFrame = coffee_df.groupby("country_of_origin").agg(
        avg_cupper   = ("cupper_points", "mean"),
        avg_yum      = ("yum_score",     "mean"),
        entry_count  = ("cupper_points", "count"),
        washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
    ).reset_index()

    aggregated_scores["pct_washed"] = aggregated_scores["washed_count"] / aggregated_scores["entry_count"]

    # Normalize each criterion to 0-1 then combine into a composite score
    for col in ["avg_cupper", "avg_yum", "pct_washed", "entry_count"]:
        col_min, col_max = aggregated_scores[col].min(), aggregated_scores[col].max()
        aggregated_scores[f"norm_{col}"] = (aggregated_scores[col] - col_min) / (col_max - col_min) if col_max != col_min else 0

    aggregated_scores["composite_score"] = (
        aggregated_scores["norm_avg_cupper"] +
        aggregated_scores["norm_avg_yum"] +
        aggregated_scores["norm_pct_washed"] +
        aggregated_scores["norm_entry_count"]
    ) / 4

    top_three_countries: list[str] = aggregated_scores.nlargest(3, "composite_score")["country_of_origin"].tolist()
    return top_three_countries

# Import the coffee ratings dataset
coffee_df: pd.DataFrame = pd.read_csv("data/results/coffee_ratings_yscore.csv")

# Import world map data
world_map: gpd.GeoDataFrame = gpd.read_file("https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")

# Define the UI for the Shiny app
app_ui = ui.page_fluid(
    # Define the dashboard title
    ui.h2("Coffee Analysis Dashboard"),
    
    # Define UI layout
    ui.layout_sidebar(

        # Define filters sidebar
        ui.sidebar(
            # Define sidebar title
            ui.h4("Filters"),

            # Add country of origin filter
            ui.input_selectize(
                "countries",
                "Country of Origin",
                choices=sorted(coffee_df["country_of_origin"].unique().tolist()),
                multiple=True
            ),

            # Add species filter
            ui.input_selectize(
                "species",
                "Species",
                choices=sorted(coffee_df["species"].unique().tolist()),
                multiple=True
            ),

            # Add processing method filter
            ui.input_selectize(
                "processing",
                "Processing Method",
                choices=sorted(coffee_df["processing"].fillna("Unknown").astype(str).unique().tolist()),
                multiple=True
            ),

            # Add numeric range filters using sliders

            # Add cupper points slider
            ui.input_slider(
                "cupper_points_range",
                "Cupper Points",
                min=float(coffee_df["cupper_points"].min()),
                max=float(coffee_df["cupper_points"].max()),
                value=[float(coffee_df["cupper_points"].min()), float(coffee_df["cupper_points"].max())]
            ),

            # Add yum score slider
            ui.input_slider(
                "yum_score_range",
                "Yum Score",
                min=float(coffee_df["yum_score"].min()),
                max=float(coffee_df["yum_score"].max()),
                value=[float(coffee_df["yum_score"].min()), float(coffee_df["yum_score"].max())]
            ),

            # Add bag weight slider
            ui.input_slider( # add a slider to filter by bag weight
                "weight_range", "Bag Weight (kg)",
                min=float(coffee_df["bag_weight"].min()),
                max=float(coffee_df["bag_weight"].max()),
                value=[float(coffee_df["bag_weight"].min()), float(coffee_df["bag_weight"].max())]
            ),

            # Set sidebar background color
            bg="#f8f9fa"
        ),
        
        # Add data table
        ui.card(
            ui.card_header("Dataset Explorer"),
            ui.output_data_frame("table"),
            height="300px"
        ),
        
        # Add scatter plot (bubble chart)
        ui.card(output_widget("chart_scatter")),

        # Add stacked bar chart and radar chart side by side
        ui.layout_column_wrap(
            ui.card(output_widget("chart_bar")),
            ui.card(output_widget("chart_radar")),
            width="1/2"
        ),

        # Add top 3 suppliers by country (Spider module)
        ui.card(  #Dunja added, connects to Spider module
            ui.card_header("Top 3 Suppliers by Country"),
            spider_ui("spiders"),
        ),


        # Add global supplier distribution map
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
    def get_filtered_coffee_df():
        filtered_coffee_df: pd.DataFrame = coffee_df.copy()

        # Apply categorical filters
        # Apply country filter
        if input.countries():
            filtered_coffee_df = filtered_coffee_df[
                filtered_coffee_df["country_of_origin"].isin(input.countries())
            ]

        # Apply species filter
        if input.species():
            filtered_coffee_df = filtered_coffee_df[
                filtered_coffee_df["species"].isin(input.species())
            ]

        # Apply processing method filter (handle NaN as "Unknown")
        if input.processing():
            filtered_coffee_df = filtered_coffee_df[
                filtered_coffee_df["processing"].fillna("Unknown").isin(input.processing())
            ]
        
        # Apply numeric range filters
        filtered_coffee_df = filtered_coffee_df[
            (filtered_coffee_df["cupper_points"] >= input.cupper_points_range()[0]) &
            (filtered_coffee_df["cupper_points"] <= input.cupper_points_range()[1])
        ]

        filtered_coffee_df = filtered_coffee_df[
            (filtered_coffee_df["yum_score"] >= input.yum_score_range()[0]) &
            (filtered_coffee_df["yum_score"] <= input.yum_score_range()[1])
        ]

        filtered_coffee_df = filtered_coffee_df[
            (filtered_coffee_df["bag_weight"] >= input.weight_range()[0]) &
            (filtered_coffee_df["bag_weight"] <= input.weight_range()[1])
        ]

        return filtered_coffee_df

    @render.data_frame
    def table():
        return render.DataGrid(get_filtered_coffee_df(), selection_mode="rows")

    # --- Chart 1: Scatter (Bubble) ---
    @render_widget
    def chart_scatter():
        filtered_coffee_df: pd.DataFrame = get_filtered_coffee_df()
        if filtered_coffee_df.empty: return go.Figure()

        # Aggregation logic adapted from visualise-coffee.py
        agg = filtered_coffee_df.groupby("country_of_origin").agg(
            avg_cupper   = ("cupper_points", "mean"),
            avg_yum      = ("yum_score",     "mean"),
            entry_count  = ("cupper_points", "count"),
            washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
        ).reset_index()
        agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]

        top3 = new_get_top3(filtered_coffee_df)
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
        filtered_coffee_df: pd.DataFrame = get_filtered_coffee_df()
        top3 = new_get_top3(filtered_coffee_df)
        if not top3: return go.Figure()
        
        d_top3 = filtered_coffee_df[filtered_coffee_df["country_of_origin"].isin(top3)].copy()
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
        filtered_coffee_df: pd.DataFrame = get_filtered_coffee_df()
        country_names = new_get_top3(filtered_coffee_df)
        if not country_names: return go.Figure()

        fig = go.Figure()
        
        # Normalize metrics for radar
        metrics = []
        for country in country_names:
            sub = filtered_coffee_df[filtered_coffee_df["country_of_origin"] == country]
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
    
    spider_server("spiders", filtered_df=get_filtered_coffee_df)

    
    # --- Map Plot ---
    @render_widget
    def map_plot():
        filtered_coffee_df: pd.DataFrame = get_filtered_coffee_df()
        if filtered_coffee_df.empty: return go.Figure()
        
        counts = filtered_coffee_df['country_of_origin'].value_counts().reset_index()
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
            title_text=f"Supplier Locations (Total: {len(filtered_coffee_df)})",
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth'
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        return fig

# Initialise Shiny App
app = App(app_ui, server)

if __name__ == "__main__":
    run_app(app, launch_browser=True)
