import requests
import geojson
from pathlib import Path

query = """
[out:json];
area["name"="Sachsen"]["boundary"="administrative"]["admin_level"="4"]->.a;
relation["name"="Dresden"]["boundary"="administrative"]["admin_level"="6"](area.a);
out geom;
"""

response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})

if response.status_code != 200:
    print(" Overpass API nicht erreichbar.")
    exit(1)

data = response.json()
if not data.get("elements"):
    print(" Keine Stadtgrenze für Dresden gefunden.")
    exit(0)

element = data["elements"][0]
coordinates = []

for member in element.get("members", []):
    if member["type"] == "way" and "geometry" in member:
        coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
        coordinates.append(coords)

feature = geojson.Feature(
    geometry=geojson.MultiPolygon([coordinates]),
    properties={"name": "Dresden Stadtgrenze"}
)
geojson_obj = geojson.FeatureCollection([feature])

output_path = Path("C:/Users/benab/.vscode/extensions/Dev/Project2/dresden_grenze.geojson")
with open(output_path, "w", encoding="utf-8") as f:
    geojson.dump(geojson_obj, f, indent=2)

print(f" Stadtgrenze gespeichert unter: {output_path.resolve()}")

