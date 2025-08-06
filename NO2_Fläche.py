import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path


def safe_float(value):
    try:
        num = float(str(value).replace(",", "."))
        return round(num, 2) if num > 0 else None
    except:
        return 0.0
            
# Pfade
input_files = [
    ("NO2 - flächenhafte Belastung (2011).csv", "2011"),
    ("NO2 - flächenhafte Belastung (2013).csv", "2013"),
    ("NO2 - flächenhafte Belastung (2015).csv", "2015"),
    ("NO2 - flächenhafte Belastung (2019).csv", "2019")
]

output_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
output_dir.mkdir(parents=True, exist_ok=True)

# Funktion zur WKT-Bereinigung
def clean_wkt(wkt_str):
    return wkt_str.split(";", 1)[-1] if isinstance(wkt_str, str) and wkt_str.startswith("SRID=") else wkt_str

# Verarbeitung pro Datei
for file_name, jahr in input_files:
    try:
        print(f"🔄 Verarbeite: {file_name}")
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')

        # Geometrien umwandeln
        df['geometry'] = df['shape'].apply(lambda s: wkt.loads(clean_wkt(s)))
        gdf = gpd.GeoDataFrame(df[['deskn1']], geometry=df['geometry'], crs="EPSG:4326")
        gdf = gdf.rename(columns={"deskn1": "NO2"})
        gdf["NO2"] = gdf["NO2"].apply(safe_float)
        gdf["Jahr"] = jahr

        # Exportieren
        output_path = output_dir / f"no2_flaeche_{jahr}.geojson"
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"✅ Gespeichert: {output_path.name}")

    except Exception as e:
        print(f"❌ Fehler in Datei {file_name}: {e}")
