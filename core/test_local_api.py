"""Call the local API and save selected time-series results as CSV files."""

import csv
from itertools import zip_longest
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

url = "http://localhost:8000/simulate2"
payload = {
    "experiment": "Simulation",
    "inputs": {
        "hhWasteRate": 0.2196,
        "fsWasteRate": 0.2156,
        "rdWasteRate": 0.0292,
        "pmWasteRate": 0.4594,
        "ppWasteRate": 0.24,
        "exPost1FLW": 0.39,
        "exPost2FLW": 0.29,
        "AverageDailyConsumption": 1.563,
    },
}


def save_columns(columns, filename):
    """Write a dictionary of equally related series to one CSV file."""
    if not columns:
        return

    path = OUTPUT_DIR / filename
    headers = list(columns)
    rows = zip_longest(*(columns[header] for header in headers), fillvalue="")

    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Created {path}")


print("Requesting a simulation...")
try:
    response = requests.post(url, json=payload, timeout=600)
    if response.status_code == 200:
        data = response.json().get("results", {})
        groups = {
            "flw_comparison": {},
            "fsc_share": {},
        }

        for key, content in data.items():
            if not isinstance(content, dict) or "dataX" not in content:
                continue

            if "flw_generated_and_flw_avoided" in key:
                column_name = key.split("|")[-1].upper()
                groups["flw_comparison"].setdefault("Day", content["dataX"])
                groups["flw_comparison"][column_name] = content["dataY"]
            elif "share_of_flw_generated" in key:
                column_name = key.split("|")[-1].capitalize()
                groups["fsc_share"].setdefault("Day", content["dataX"])
                groups["fsc_share"][column_name] = content["dataY"]

        save_columns(groups["flw_comparison"], "flw_generated_vs_avoided.csv")
        save_columns(groups["fsc_share"], "flw_share_by_stage.csv")
    else:
        print(f"The API returned HTTP {response.status_code}: {response.text}")
except requests.RequestException as exc:
    print(f"The request failed: {exc}")
