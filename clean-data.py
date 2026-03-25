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

    # Clean processing_method values
    processing_methods_mapping: dict[str, str] = {
        "Natural / Dry": "Natural",
        "Pulped natural / honey": "Pulped-Natural",
        "Semi-washed / Semi-pulped": "Semi-Washed",
        "Washed / Wet": "Washed",
    }

    if "processing_method" in coffee_ratings_cleaned_df.columns:
        print("Cleaning processing_method values...")
        coffee_ratings_cleaned_df["processing_method"] = coffee_ratings_cleaned_df["processing_method"].map(processing_methods_mapping)

    # Export cleaned DataFrame to a new CSV file
    print("Exporting cleaned data to CSV...")
    coffee_ratings_cleaned_df.to_csv(export_csv_filename, index=False)


if __name__ == "__main__":
    main()