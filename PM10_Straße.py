import pandas as pd
import json
from pathlib import Path
from utils import linestring_to_coordinates, safe_float

# Verzeichnis definieren
input_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
output_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
output_dir.mkdir(parents=True, exist_ok=True)

# CSV-Dateien mit Jahr
pm10_strasse_files = {
    "2011": "PM10 - Straßenrandbelastung (2011).csv",
    "2013": "PM10 - Straßenrandbelastung (2013).csv",
    "2015": "PM10 - Straßenrandbelastung (2015).csv",
    "2019": "PM10 - Straßenrandbelastung (2019).csv"
}

# CSVs verarbeiten und GeoJSON erzeugen
for jahr, filename in pm10_strasse_files.items():
    path = input_dir / filename
    df = pd.read_csv(path, sep=';', encoding='utf-8')

    # Einheitliche Spalte "pm10_ist" erzeugen
    if jahr == "2019":
        if "deskn1" in df.columns:
            df = df.rename(columns={"deskn1": "pm10_ist"})
        else:
            raise ValueError(f 'deskn1' fehlt in Datei {filename}")

    features = []
    for _, row in df.iterrows():
        coords = linestring_to_coordinates(row['shape'])
        if not coords:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "properties": {
                "strname": row.get("strname", ""),
                "pm10_ist": safe_float(row.get("pm10_ist", "")),
                "jahr": jahr
            }
        }
        features.append(feature)

    geojson_obj = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = output_dir / f"pm10_strasse_{jahr}.geojson"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson_obj, f, ensure_ascii=False, indent=2)


    print(f" Gespeichert: {output_file.name}")
