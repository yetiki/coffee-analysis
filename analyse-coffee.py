import csv
import pandas as pd
from pathlib import Path
from yum_score_funcs import normalise_points, yum_score

def main(input_csv_file: str = "data/clean/coffee_ratings.csv", output_csv_file: str = "data/clean/coffee_ratings_yscore.csv"):
    # Normalise filename paths
    input_csv_file: Path = Path(input_csv_file)
    output_csv_file: Path = Path(output_csv_file)

    # Ensure import filename exists
    if not input_csv_file.is_file():
        print(f"Error: Input file '{input_csv_file}' does not exist.")
        return
    
    # Ensure export directory exists and create if it doesn't
    output_csv_file.parent.mkdir(parents=True, exist_ok=True)

    ### Getting the min and max values
    df = pd.read_csv(input_csv_file)
    max_aroma = df["aroma"].max()
    min_aroma = df["aroma"].min()
    max_flavor = df["flavor"].max()
    min_flavor = df["flavor"].min()
    max_body = df["body"].max()
    min_body = df["body"].min()
    max_uniformity = df["uniformity"].max()
    min_uniformity = df["uniformity"].min()


    ### calculating all the yum scores and adding it to a new csv
    with open(input_csv_file, "r") as infile, open(output_csv_file, "w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        ### Read and modify the header to add a yum-score column ###
        header = next(reader)
        header.append("yum-score")
        writer.writerow(header)

        ### Loop through remaining rows to calculate the yum score ###
        for row in reader:
            aroma_points = normalise_points(min_aroma, max_aroma, float(row[5]))
            flavor_points = normalise_points(min_flavor, max_flavor, float(row[6]))
            body_points = normalise_points(min_body, max_body, float(row[7]))
            uniformity_points = normalise_points(min_uniformity, max_uniformity, float(row[8]))
            y_score = yum_score(aroma_points, flavor_points, body_points, uniformity_points)
            row.append(round(y_score,2))
            writer.writerow(row)

if __name__ == "__main__":
    main()