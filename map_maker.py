import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# 1. Load the clean data
coffee_ratings = pd.read_csv('data/clean/coffee_ratings.csv')

# 2. Count frequencies and convert to a clean DataFrame
country_counts = coffee_ratings['country_of_origin'].value_counts().reset_index()
country_counts.columns = ['country_name', 'rating_count'] # Explicitly name the columns

# 3. Load the world map directly from the Natural Earth URL (Fixes the deprecation)
url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url)

# 4. Merge the datasets
# Note: The Natural Earth dataset uses uppercase 'ADMIN' or 'NAME' for country names. 
# 'ADMIN' is usually the most reliable for matching sovereign states.
world = world.merge(country_counts, how='left', left_on='ADMIN', right_on='country_name')

# 5. Plot the world map
fig, ax = plt.subplots(1, 1, figsize=(15, 10))

# Notice we are now plotting the 'rating_count' column
world.plot(
    column='rating_count', 
    ax=ax, 
    legend=False, 
    cmap='OrRd', 
    missing_kwds={'color': 'lightgrey'}
)

ax.set_title('Frequency of Coffee Ratings by Country of Origin')
ax.set_axis_off() # Optional: Turns off the lat/long axis box for a cleaner look
plt.show()