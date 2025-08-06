import pandas as pd
import json
import re
from pathlib import Path

def safe_float(value):
    try:
        num = float(str(value).replace(",", "."))
        return round(num, 2) if num > 0 else None
    except:
        return 0.0

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

# Funktion zum Parsen von LINESTRING
def linestring_to_coordinates(linestring):
    match = re.search(r'LINESTRING\s*\(([^)]+)\)', linestring)
    if not match:
        return []
    coord_pairs = match.group(1).split(',')
    coords = []
    for pair in coord_pairs:
        parts = pair.strip().replace('(', '').replace(')', '').split()
        if len(parts) == 2:
            try:
                lon = float(parts[0].replace(",", "."))
                lat = float(parts[1].replace(",", "."))
                coords.append([lon, lat])
            except Exception:
                continue
    return coords

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
