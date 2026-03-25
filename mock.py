# A script which takes the raw data and creates a clean dataset for analysis. 
# The cleaning can be hardcoded here; more thorough cleaning will be done by Yoshi.
# take raw data and filter it to only be the nice columns 

import pandas as pd

# Load the raw data
raw_data = pd.read_csv('data/simplified_coffee_ratings.csv')

# filter to only the columns we want to keep
# Country, Species, Processing, CuppaPoints, YumScore. 

# print column names to check for typos
print(raw_data.columns)
# Index(['species', 'owner', 'country_of_origin', 'farm_name', 'lot_number',
#        'mill', 'company', 'altitude', 'region', 'producer', 'number_of_bags',
#        'bag_weight', 'in_country_partner', 'harvest_year', 'grading_date',
#        'owner_1', 'variety', 'processing_method', 'aroma', 'flavor',
#        'aftertaste', 'acidity', 'body', 'balance', 'uniformity', 'clean_cup',
#        'sweetness', 'cupper_points', 'moisture'],
#       dtype='object')

# filter to only the columns we want to keep
filtered_data = raw_data[['country_of_origin', 'species', 'processing_method', 'cupper_points']].copy()

# add a new column which is the scores from flavour body aroma uniformity all scaled to be 0-1 and averaged to be the "YumScore"
filtered_data['YumScore'] = (raw_data['flavor'] + raw_data['body'] + raw_data['aroma'] + raw_data['uniformity']) / 4 / 10

# head filtered data to check it looks right
print(filtered_data.head())

# count na's per column to check for missing values
print(filtered_data.isna().sum())

# print dimentions
print(filtered_data.shape)

# save the filtered data to a new csv
# called "mock_cleaned_coffee_ratings.csv"