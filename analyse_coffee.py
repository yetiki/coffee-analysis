import csv
import pandas as pd
from pathlib import Path


### normalise_points() returns a score from 0-1
def normalise_points(min, max, score):
    normal_points = (score - min) / (max - min)
    return normal_points


### yum_score() returns a score from 0-1
def yum_score(a_points, f_points, b_points, u_points):
    total_points = (a_points + f_points + b_points + u_points) / 4  # FIX 1: brackets around all 4
    return total_points


### get_top3() returns the top 3 country names as a list of strings
### This is imported by visualise_coffee.py
def get_top3(csv_file: str = "data/results/coffee_ratings_yscore.csv"):
    df = pd.read_csv(csv_file)

    agg = df.groupby("country_of_origin").agg(
        avg_cupper   = ("cupper_points", "mean"),
        avg_yum      = ("yum_score",     "mean"),
        entry_count  = ("cupper_points", "count"),
        washed_count = ("processing",    lambda x: (x.str.lower() == "washed").sum())
    ).reset_index()

    agg["pct_washed"] = agg["washed_count"] / agg["entry_count"]

    # Normalise each criterion to 0-1 then combine into a composite score
    for col in ["avg_cupper", "avg_yum", "pct_washed", "entry_count"]:
        col_min, col_max = agg[col].min(), agg[col].max()
        agg[f"norm_{col}"] = (agg[col] - col_min) / (col_max - col_min)

    agg["composite_score"] = (
        agg["norm_avg_cupper"]  +
        agg["norm_avg_yum"]     +
        agg["norm_pct_washed"]  +
        agg["norm_entry_count"]
    ) / 4

    top3 = agg.nlargest(3, "composite_score")["country_of_origin"].tolist()
    return top3

def main(
    input_csv_file:  str = "data/clean/coffee_ratings.csv",
    output_csv_file: str = "data/results/coffee_ratings_yscore.csv"
):
    input_csv_file:  Path = Path(input_csv_file)
    output_csv_file: Path = Path(output_csv_file)

    if not input_csv_file.is_file():
        print(f"Error: Input file '{input_csv_file}' does not exist.")
        return

    output_csv_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv_file)
    max_aroma      = df["aroma"].max()
    min_aroma      = df["aroma"].min()
    max_flavour    = df["flavor"].max()
    min_flavour    = df["flavor"].min()
    max_body       = df["body"].max()
    min_body       = df["body"].min()
    max_uniformity = df["uniformity"].max()
    min_uniformity = df["uniformity"].min()

    with open(input_csv_file, "r") as infile, open(output_csv_file, "w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        header = next(reader)
        
        # --- FIX 1: Rename 'processing_method' to 'processing' ---
        if "processing_method" in header:
            idx = header.index("processing_method")
            header[idx] = "processing"
            
        # --- FIX 2: Add 'cupper_points' to the header ---
        header.append("cupper_points")
        header.append("yum_score")   # (Your existing fix)
        writer.writerow(header)

        for row in reader:
            # Extract raw floats first so we can use them for both calculations
            aroma_raw      = float(row[5])
            flavour_raw    = float(row[6])
            body_raw       = float(row[7])
            uniformity_raw = float(row[8])
            
            # --- FIX 3: Calculate cupper_points (average of 4 raw metrics) ---
            c_points = (aroma_raw + flavour_raw + body_raw + uniformity_raw) / 4

            # Calculate yum_score using your functions
            aroma_points      = normalise_points(min_aroma,      max_aroma,      aroma_raw)
            flavour_points    = normalise_points(min_flavour,    max_flavour,    flavour_raw)
            body_points       = normalise_points(min_body,       max_body,       body_raw)
            uniformity_points = normalise_points(min_uniformity, max_uniformity, uniformity_raw)
            
            y_score = yum_score(aroma_points, flavour_points, body_points, uniformity_points)
            
            # Append BOTH metrics to the end of the row
            row.append(round(c_points, 2))
            row.append(round(y_score, 2))
            
            writer.writerow(row)

    print(f"Done - cupper points and yum scores written to {output_csv_file}")

if __name__ == "__main__":
    main()