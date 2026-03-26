
````md
# Coffee Supplier Analysis Dashboard
**Internal Decision Support Tool for Dr. Cappuccino**

## Description
This project is a custom, interactive data analysis dashboard built with **Shiny for Python**. It was commissioned as an internal tool to empower Dr. Cappuccino and his procurement team to evaluate, filter, and select the optimal global coffee suppliers for his expanding shop. 

The application utilizes a custom scoring algorithm that synthesizes raw quality metrics (aroma, flavor, body, uniformity) into a proprietary `YumScore`, weighting inputs based on the client's specific flavor profile requirements.

### Dashboard Layout & Key Features
The dashboard provides a seamless flow from high-level global metrics down to individual country profiles:

* **Interactive Data Explorer (Table):** An interactive, filterable grid where **each row represents a specific country**, and the columns display the aggregated statistics and metrics we want to evaluate.
* **The "Hero" Visual (Scatter-Bubble Plot):** A comprehensive view aggregating every country into a single plot.
    * **X-Axis:** Average Cupper Points
    * **Y-Axis:** Average `YumScore`
    * **Bubble Size:** Number of entries (proxy for producer volume/reliability)
    * **Color Intensity:** Percentage of washed processing
    * *Insight:* This instantly highlights the top 3 recommended countries with annotated labels, combining all four of the client's criteria into a single, actionable view.
* **Country Performance (Bubble Bar Chart):** A dedicated chart where the X-axis is the country name and the Y-axis is the `YumScore` (the average score among aroma, uniformity, body, and flavor).
* **Profile Comparison (3x3 Spider Charts):** A set of customized spider charts providing a clean, "at-a-glance" visual profile of the top suppliers and countries, making the final recommendations obvious for executive decision-making.
* **Global Supplier Map:** A dynamic choropleth world map where each country containing a supplier is colored. The color intensity is proportional to the number of suppliers in that region. This map updates in real-time to reflect any active filters applied to the main table.

## Data Source
The tool leverages data from the [Coffee Quality Institute](https://database.coffeeinstitute.org/), synthesized by Data Scientist James LeDoux into the [Coffee Quality Database GitHub Repository](https://github.com/jldbc/coffee-quality-database).

## Pre-requisites
All software dependencies are strictly version-controlled in `requirements.txt`. It is recommended to run this project in a Python virtual environment.

## Installation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/yourusername/coffee-analysis.git](https://github.com/yourusername/coffee-analysis.git)
cd coffee-analysis
pip install -r requirements.txt
````

## Usage

**1. Launching the Interactive Dashboard**
To start the local server and launch the Shiny app, run the following command in your terminal:

```bash
python app.py
```

*(The dashboard should open automatically in your default web browser. If not, navigate to the local URL provided in your terminal, typically `http://127.0.0.1:8000`)*

**2. Running Background Analysis (Optional CLI)**
If you need to re-run the core scoring and ranking algorithm via the command line with specific constraints:

```bash
python analyse-coffee.py location=UK minimum_kg=100
```

*Available CLI arguments:*

  * `location`: Filter by country of origin (e.g., 'Brazil', 'Ethiopia').
  * `minimum_kg`: Filter by minimum bag weight available from the supplier.

## Testing

To ensure data integrity and algorithm accuracy, run the test suite:

```bash
python tests.py
```

*Expected output: `all good!`*

## Maintainers

  - **Current Maintainer:** [YOSHI]
  - **Original Author:** NeDoYeMo

## Acknowledgements

  - James LeDoux for the Coffee Quality Database.

## License

This project is licensed under the **MIT License**. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
