import pandas as pd
from pathlib import Path


def main(
        input_csv_filename: str = "data/raw/simplified_coffee_ratings.csv",
        columns: list[str] = [
            "species",
            "country_of_origin",
            "number_of_bags",
            "bag_weight",
            "processing_method",
            "aroma",
            "flavor",
            "body",
            "uniformity",
        ],
        export_csv_filename: str = "data/clean/coffee_ratings.csv",
) -> None:
    """
    Main function to clean the coffee ratings data.

    Parameters
    ----------
    input_csv_filename : str
        The filename of the input CSV file containing the raw coffee ratings data.

    columns : list[str]
        The list of columns to select and clean from the raw data.

    export_csv_filename : str
        The filename of the output CSV file to save the cleaned coffee ratings data.

    Returns
    -------
    None
        This function does not return any value. It reads the raw data, cleans it, and saves the cleaned data to a new CSV file.
    """
    # Normalise filename paths
    input_csv_filename: Path = Path(input_csv_filename)
    export_csv_filename: Path = Path(export_csv_filename)

    # Ensure import filename exists
    if not input_csv_filename.is_file():
        print(f"Error: Input file '{input_csv_filename}' does not exist.")
        return
    
    # Ensure export directory exists and create if it doesn't
    export_csv_filename.parent.mkdir(parents=True, exist_ok=True)

    # Import coffee ratings raw data as a DataFrame
    coffee_ratings_df: pd.DataFrame = pd.read_csv(input_csv_filename)

    # Check if specified columns exist in the DataFrame
    missing_columns: list[str] = [col for col in columns if col not in coffee_ratings_df.columns]
    if missing_columns:
        print(f"Error: The following specified columns are missing from the input data: {missing_columns}")
        return

    # Select only the specified columns for cleaning
    coffee_ratings_cleaned_df: pd.DataFrame = coffee_ratings_df[columns]

    # Check for missing values
    n_missing_rows: int = coffee_ratings_cleaned_df.isnull().any(axis=1).sum()
    print(f"Found {n_missing_rows} rows with missing values.")

    # Drop rows with missing values
    print("Removing rows with missing values...")
    coffee_ratings_cleaned_df = coffee_ratings_cleaned_df.dropna()
    print(f"Removed {n_missing_rows} rows with missing values.")

    # Check for duplicates
    n_duplicates: int = coffee_ratings_cleaned_df.duplicated().sum()
    print(f"Found {n_duplicates} duplicate rows.")

    # Drop duplicates
    print("Removing duplicate rows...")
    coffee_ratings_cleaned_df = coffee_ratings_cleaned_df.drop_duplicates()
    print(f"Removed {n_duplicates} duplicate rows.")

    # Normalise processing_method values

    if "processing_method" in coffee_ratings_cleaned_df.columns:
        print("Normalising processing_method values...")
        coffee_ratings_cleaned_df["processing_method"] = coffee_ratings_cleaned_df["processing_method"].apply(normalise_processing_methods)

    # Normalise units for bag_weight to kilograms
    if "bag_weight" in coffee_ratings_cleaned_df.columns:
        print("Normalising bag_weight units to kilograms...")
        coffee_ratings_cleaned_df["bag_weight"] = coffee_ratings_cleaned_df["bag_weight"].apply(normalise_bag_weights)

    # Export cleaned DataFrame to a new CSV file
    print("Exporting cleaned data to CSV...")
    coffee_ratings_cleaned_df.to_csv(export_csv_filename, index=False)


def pounds_to_kilograms(pounds: float) -> float:
    """Convert pounds to kilograms."""
    return pounds * 0.453592


def normalise_bag_weights(bag_weight: str) -> float:
    """
    Normalise bag weight values to kilograms.
    Converts string values with "kg" or "lbs" units to float values in kilograms.

    Parameters
    ----------
    bag_weight : str
        The bag weight as a string, e.g., "60 kg" or "132 lbs".

    Returns
    -------
    float
        The bag weight in kilograms.

    Raises   
    ------
    ValueError
        If the bag weight string does not contain a recognized unit ("kg" or "lbs").
    """
    if "kg" in bag_weight:
        return float(bag_weight.replace("kg", "").strip())
    
    elif "lbs" in bag_weight:
        return pounds_to_kilograms(float(bag_weight.replace("lbs", "").strip()))
    
    else:
        raise ValueError(f"Unknown weight unit in '{bag_weight}'")


def normalise_processing_methods(processing_method: str) -> str:
    """
    Normalise processing method values to a standard set of categories.

    Parameters
    ----------
    processing_method : str
        The original processing method value.

    Returns
    -------
    str
        The normalised processing method value.
    """
    processing_methods_mapping: dict[str, str] = {
        "Natural / Dry": "Natural",
        "Pulped natural / honey": "Pulped-Natural",
        "Semi-washed / Semi-pulped": "Semi-Washed",
        "Washed / Wet": "Washed",
    }
    
    return processing_methods_mapping.get(processing_method, processing_method)

if __name__ == "__main__":
    main()