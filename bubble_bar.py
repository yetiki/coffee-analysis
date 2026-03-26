import pandas as pd
import plotly.graph_objects as go

def create_bubble_chart(data_path="data/results/coffee_ratings_yscore.csv", n_countries=5):
    """
    Creates and returns a bubble bar chart for the app.py file.
    """
    # load data
    df = pd.read_csv(data_path)

    # check column names
    print("Columns in the dataset:", df.columns.tolist())

    # order by yum score
    df = df.sort_values(by="yum_score", ascending=False) 

    # compute average flavor score by country and keep top n_countries
    avg_yum_by_country = df.groupby('country_of_origin')['yum_score'].mean()
    top_countries = avg_yum_by_country.nlargest(n_countries).index

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
        method_rows = filtered_suppliers[filtered_suppliers['processing'] == method]
        if method_rows.empty:
            continue
        fig.add_trace(go.Scatter(
            x=method_rows['country_of_origin'],
            y=method_rows['yum_score'],
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
        title=f"Yum score by Country (Top {n_countries} countries by avg yum score)",
        xaxis_title="Country of Origin",
        yaxis_title="Yum Score",
        template="plotly_white"
    )

    return fig

if __name__ == '__main__':
    
    # Test the standalone function
    fig = create_bubble_chart(data_path="data/results/coffee_ratings_yscore.csv", n_countries=5)
    fig.show()

