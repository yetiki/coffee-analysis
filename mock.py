# A script which takes the raw data and creates a clean dataset for analysis. 
# The cleaning can be hardcoded here; more thorough cleaning will be done by Yoshi.
# take raw data and filter it to only be the nice columns 

import pandas as pd

# Load the raw data
raw_data = pd.read_csv('data/simplified_coffee_ratings.csv')

# filter to only the columns we want to keep
# Country, Species, Processing, CuppaPoints, YumScore. 

# print column names to check for typos
# print(raw_data.columns)
# Index(['species', 'owner', 'country_of_origin', 'farm_name', 'lot_number',
#        'mill', 'company', 'altitude', 'region', 'producer', 'number_of_bags',
#        'bag_weight', 'in_country_partner', 'harvest_year', 'grading_date',
#        'owner_1', 'variety', 'processing_method', 'aroma', 'flavor',
#        'aftertaste', 'acidity', 'body', 'balance', 'uniformity', 'clean_cup',
#        'sweetness', 'cupper_points', 'moisture'],
#       dtype='object')

# filter to only the columns we want to keep
# also keep the columns flavour, body, aroma, uniformity to create the "YumScore" which is the average of these 4 columns scaled to be between 0 and 1.
filtered_data = raw_data[['country_of_origin', 'species', 'processing_method', 'cupper_points', 'flavor', 'body', 'aroma', 'uniformity']].copy()

# add a new column which is the scores from flavour body aroma uniformity all scaled to be 0-1 and averaged to be the "YumScore"
filtered_data['YumScore'] = (filtered_data['flavor'] + filtered_data['body'] + filtered_data['aroma'] + filtered_data['uniformity']) / 4 / 10

# # head filtered data to check it looks right
# print(filtered_data.head())

# # count na's per column to check for missing values
# print(filtered_data.isna().sum())

# # print dimentions
# print(filtered_data.shape)

# remove the row where country is na
filtered_data = filtered_data.dropna(subset=['country_of_origin'])

# save the filtered data to a new csv
# called "mock_cleaned_coffee_ratings.csv"
filtered_data.to_csv('data/mock_cleaned_coffee_ratings.csv', index=False)