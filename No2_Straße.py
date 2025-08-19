import pandas as pd
import json
from pathlib import Path
from utils import linestring_to_coordinates, safe_float

# CSV-Dateien mit Jahr
csv_files = {
    "2011": "NO2 - Straßenrandbelastung (2011).csv",
    "2013": "NO2 - Straßenrandbelastung (2013).csv",
    "2015": "NO2 - Straßenrandbelastung (2015).csv",
    "2019": "NO2 - Straßenrandbelastung (2019).csv"
}

# Ausgabeordner
output_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
output_dir.mkdir(parents=True, exist_ok=True)

# Verarbeite jede CSV
for jahr, filename in csv_files.items():
    print(f"🔄 Verarbeite {filename} ...")
    try:
        df = pd.read_csv(filename, sep=';', encoding='utf-8')
        features = []

        for _, row in df.iterrows():
            coords = linestring_to_coordinates(row['shape'])
            if not coords:
                continue

            # Wähle die richtige NO2-Spalte basierend auf dem Jahr
            no2_value = row.get("deskn1", "") if jahr == "2019" else row.get("no2_i1", "")

            properties = {
                "strname": row.get("strname", ""),
                "no2_i1": safe_float(no2_value),
                "jahr": jahr
            }

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": properties
            }

            features.append(feature)

        geojson_obj = {
            "type": "FeatureCollection",
            "features": features
        }

        # Speichern
        out_path = output_dir / f"no2_strasse_{jahr}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson_obj, f, ensure_ascii=False, indent=2)

        print(f"✅ Gespeichert: {out_path.name}")

    except Exception as e:
        print(f"❌ Fehler bei {filename}: {e}")