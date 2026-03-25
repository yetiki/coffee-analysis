import csv
import pandas as pd
from pathlib import Path

### normalise_points() returns a score from 0-1
def normalise_points(min, max, score):
    normal_points = (score - min)/(max - min)
    return normal_points

### yum_score() returns a score from 0-1
def yum_score(a_points, f_points, b_points, u_points):
    total_points = a_points + f_points + b_points + u_points
    y_score = total_points / 4
    return y_score

def main(input_csv_file: str = "data/clean/coffee_ratings.csv", output_csv_file: str = "data/results/coffee_ratings_yscore.csv"):
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
    max_flavour = df["flavor"].max()
    min_flavour = df["flavor"].min()
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
            flavour_points = normalise_points(min_flavour, max_flavour, float(row[6]))
            body_points = normalise_points(min_body, max_body, float(row[7]))
            uniformity_points = normalise_points(min_uniformity, max_uniformity, float(row[8]))
            y_score = yum_score(aroma_points, flavour_points, body_points, uniformity_points)
            row.append(round(y_score,2))
            writer.writerow(row)

if __name__ == "__main__":
    main()