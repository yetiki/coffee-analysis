import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt

def create_bubble_chart(data_path="data/clean/coffee_ratings.csv", n_countries=6):
    """
    Creates and returns a bubble bar chart for the app.py file.
    """
    # load data
    df = pd.read_csv(data_path)

    # filter out any rows with total weight greater than 1000 kg to remove outliers
    df = df[df['total_weight'] <= 1000]

    # order by flavour (it should be yum score once we have that)
    df = df.sort_values(by="flavor", ascending=False) 

    # compute average flavor score by country and keep top n_countries
    avg_flavor_by_country = df.groupby('country_of_origin')['flavor'].mean()
    top_countries = avg_flavor_by_country.nlargest(n_countries).index

    # filter original data to only include rows for those top countries
    filtered_suppliers = df[df['country_of_origin'].isin(top_countries)]

    # build a plot 
    color_map = {
        'Washed': 'blue',
        'Natural': 'green',
        'Semi-Washed': 'yellow',
        'Pulped-Natural': 'purple',
        'Other': 'gray'
    }

    fig = go.Figure()
    for method, color in color_map.items():
        method_rows = filtered_suppliers[filtered_suppliers['processing_method'] == method]
        if method_rows.empty:
            continue
        fig.add_trace(go.Scatter(
            x=method_rows['country_of_origin'],
            y=method_rows['flavor'],
            mode='markers',
            name=method,
            marker=dict(
                size=method_rows['total_weight'].astype(float),
                color=color,
                opacity=0.7,
                sizemode='area',
                sizeref=2.*filtered_suppliers['total_weight'].max()/(40.**2)
            )
        ))

    # legend automatically shows which color corresponds to which processing method
    fig.update_layout(
        title=f"Flavor score by Country (Top {n_countries} countries by avg flavor score)",
        xaxis_title="Country of Origin",
        yaxis_title="Flavor Score",
        template="plotly_white"
    )

    return fig

if __name__ == '__main__':
    
    # Test the standalone function
    fig = create_bubble_chart(data_path="data/clean/coffee_ratings.csv", n_countries=6)
    fig.show()

