import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

# 1. Define the Regex Patterns
# Added |p\.s\.n\.m\.? to the end to catch the dotted Spanish abbreviation
feet_pattern = r'\b(ft|feet|pies|psn|psnm|f)\b|p\.s\.n\.m\.?'
metre_pattern = r'\b(m|mts|m公尺|masl|msnm|meter|meters|metres|metros|mals|msm|msn|msl|msnn|snn|mosl|mtr|mtrs|dpl|公尺)\b|m\.s\.n\.m|m\.s\.l|a\.s\.l'
range_pattern = r'(\d+\.?\d*)\s*[a-zA-Z]*\s*(?:-|\bto\b|\band\b|\bthru\b|~|\ba\b)\s*\d+\.?\d*\s*(.*)'

def standardise_altitude(val):
    """
    Cleans altitude strings, flattens ranges, and converts valid entries 
    to a standard metric float. Returns NaN for ambiguous data.
    """
    if pd.isna(val):
        return np.nan
        
    val = str(val).lower().strip()
    
    # 2. Space Injection (Separate numbers from glued units like "1000m" or "950公尺")
    val = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', val)
    val = re.sub(r'(\d)(公尺)', r'\1 \2', val)
    
    # 3. Flatten Ranges (Keep the first number and the trailing unit)
    val = re.sub(range_pattern, r'\1 \2', val)
    
    # 4. Determine the Unit
    is_feet = bool(re.search(feet_pattern, val))
    is_metre = bool(re.search(metre_pattern, val))
    
    # Strict rejection: If it has no units, or conflicting units, drop it
    if (not is_feet and not is_metre) or (is_feet and is_metre):
        return np.nan
        
    # 5. Clean Formatting (Remove standard commas and European thousands separators)
    val = val.replace(',', '')
    val = re.sub(r'(?<=\d)\.(?=\d{3}\b)', '', val)
    
    # 6. Extract the Number Safely
    numbers = re.findall(r'\d+\.?\d*', val)
    if not numbers:
        return np.nan
        
    num = float(numbers[0])
    
    # 7. Convert Feet to Metres
    if is_feet:
        num = num * 0.3048
        
    # 8. Sanity Cap (Reject impossible terrestrial altitudes)
    if num > 4000:
        return np.nan
        
    return round(num, 0)


# --- Execution Pipeline ---

# Load the raw data
raw_data = pd.read_csv('data/simplified_coffee_ratings.csv')

# Apply the single cleaning function and enforce the nullable integer type
raw_data['altitude_clean_metres'] = raw_data['altitude'].apply(standardise_altitude).astype('Int64')

# Display the clean range and check for missing values
clean_col = raw_data['altitude_clean_metres'].dropna()
print(f"Cleaned Data Range: {clean_col.min()}m to {clean_col.max()}m")
print(f"Data Retained: {len(clean_col)} out of {len(raw_data)} rows.")

# Show a histogram of the cleaned values
plt.figure(figsize=(10, 6))
plt.hist(clean_col, bins=50, color='skyblue', edgecolor='black')
plt.title('Distribution of Standardised Coffee Altitudes (Metres)')
plt.xlabel('Altitude (m)')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)

# Save and show plot
plt.savefig('cleaned_altitude_histogram.png')
plt.show()


# print the column names
print(raw_data.columns)
# Index(['species',  TIDY!
# 'owner',  - not relevant?
# 'country_of_origin', - Tidy, but might need to be made to match the names in the mapping software.
# 'farm_name', - not relevant?
# 'lot_number', - not relevant?
#  'mill', - not relevant?
# 'company', - not relevant?
# 'altitude', - chaos, messy fixed above.
# 'region', - chaos, not relevant?
# 'producer',
# 'number_of_bags',
# 'bag_weight',
# 'in_country_partner',
# 'harvest_year',
# 'grading_date',
# 'owner_1',
# 'variety',
# 'processing_method',
# 'aroma',
# 'flavor',
# 'aftertaste',
# 'acidity',
# 'body',
# 'balance',
# 'uniformity',
# 'clean_cup',
# 'sweetness',
# 'cupper_points',
# 'moisture',
# 'altitude_clean_metres'],
# dtype='object')

# check the unique values in each column
print(raw_data['country_of_origin'].unique())


