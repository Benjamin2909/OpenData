import streamlit as st
import pandas as pd
import folium
import json
import geopandas as gpd
from streamlit_folium import st_folium
from pathlib import Path

st.title("Interaktive Karte mit Layer-Steuerung")

def round_all_numeric_properties(geojson_data):
    for feature in geojson_data.get("features", []):
        for key, value in feature.get("properties", {}).items():
            try:
                num = float(value)
                feature["properties"][key] = round(num, 2)
            except:
                continue


# GeoJSON-Verzeichnis und Dateien
geojson_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
boundary_file = "dresden_grenze.geojson"
geojson_files = [f for f in geojson_dir.glob("*.geojson") if f.name != boundary_file]
layer_options = [f.stem for f in geojson_files]


# Layerauswahl
selected_layers = st.multiselect(
    "Wähle die Layer aus, die angezeigt werden sollen:",
    layer_options
)

# Karte erzeugen
m = folium.Map(location=[51.05, 13.74], zoom_start=12)

# Stadtgrenze laden
boundary_path = geojson_dir / boundary_file
if boundary_path.exists():
    with open(boundary_path, "r", encoding="utf-8") as f:
        boundary_geojson = json.load(f)
    folium.GeoJson(
        boundary_geojson,
        name="Stadtgrenze Dresden",
        style_function=lambda feature: {
            "color": "black",
            "weight": 2,
            "fillOpacity": 0,
        },
        control=False,
    ).add_to(m)
else:
    st.warning("dresden_grenze.geojson wurde nicht gefunden!")

# Float sicher umwandeln
def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


# Klassengrenzen-Farbfunktion
def klassierte_farbe(value, typ):
    v = safe_float(value)
    if v <= 0:
        return None
    if v > 40:
        return "#FF0000"  # Rot
    elif v > 27:
        return "#FFA500"  # Orange
    elif v > 20:
        return "#FFFF00"  # Gelb
    elif v > 15:
        return "#ADFF2F"  # Hellgrün
    else:
        return "#008000"  # Grün
    
from branca.element import Template, MacroElement

def add_color_legend(map_object):
    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 180px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        ">
        <b>NO2-/PM10-Belastung</b><br>
        <i style="background:#FF0000; width:15px; height:15px; float:left; margin-right:8px; opacity:0.8;"></i> > 40 µg/m³<br>
        <i style="background:#FFA500; width:15px; height:15px; float:left; margin-right:8px; opacity:0.8;"></i> 27 - 40 µg/m³<br>
        <i style="background:#FFFF00; width:15px; height:15px; float:left; margin-right:8px; opacity:0.8;"></i> 20 - 27 µg/m³<br>
        <i style="background:#ADFF2F; width:15px; height:15px; float:left; margin-right:8px; opacity:0.8;"></i> 15 - 20 µg/m³<br>
        <i style="background:#008000; width:15px; height:15px; float:left; margin-right:8px; opacity:0.8;"></i> ≤ 15 µg/m³<br>
    </div>
    {% endmacro %}
    """
    legend = MacroElement()
    legend._template = Template(legend_html)
    map_object.get_root().add_child(legend)


# GeoJSON-Layer verarbeiten
for layer_name in selected_layers:
    filepath = geojson_dir / f"{layer_name}.geojson"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        round_all_numeric_properties(geojson_data) 

        # NO₂ Fläche
        if "no2" in layer_name and "flaeche" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["NO2", "Jahr"],
                aliases=["NO₂-Belastung (µg/m³):", "Jahr:"]
            )
            style_fn = lambda feature: {
                "fillColor": klassierte_farbe(feature["properties"].get("NO2"), "no2"),
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6
            }
            folium.GeoJson(
                geojson_data,
                name=layer_name,
                tooltip=tooltip,
                style_function=style_fn
            ).add_to(m)

        # NO₂ Straße
        elif "no2" in layer_name and "strasse" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["no2_i1", "jahr"],
                aliases=["NO₂-Belastung (µg/m³):", "Jahr:"]
            )
            valid_features = [f for f in geojson_data["features"]
                            if safe_float(f["properties"].get("no2_i1")) > 0]

            if valid_features:
                def style_fn(feature):
                    return {
                        "color": klassierte_farbe(feature["properties"].get("no2_i1"), "no2"),
                        "weight": 3
                    }

                folium.GeoJson(
                    {"type": "FeatureCollection", "features": valid_features},
                    name=layer_name,
                    tooltip=tooltip,
                    style_function=style_fn
                ).add_to(m)

        # PM10 Fläche
        elif "pm10" in layer_name and "flaeche" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["PM10", "Jahr"],
                aliases=["PM10-Belastung (µg/m³):", "Jahr:"]
            )
            style_fn = lambda feature: {
                "fillColor": klassierte_farbe(feature["properties"].get("PM10"), "pm10"),
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6
            }
            folium.GeoJson(
                geojson_data,
                name=layer_name,
                tooltip=tooltip,
                style_function=style_fn
            ).add_to(m)

        # PM10 Straße
        elif "pm10" in layer_name and "strasse" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["pm10_ist", "jahr"],
                aliases=["PM10-Belastung (µg/m³):", "Jahr:"]
            )
            valid_features = [f for f in geojson_data["features"]
                            if safe_float(f["properties"].get("pm10_ist")) > 0]

            if valid_features:
                def style_fn(feature):
                    return {
                        "color": klassierte_farbe(feature["properties"].get("pm10_ist"), "pm10"),
                        "weight": 3
                    }

                folium.GeoJson(
                    {"type": "FeatureCollection", "features": valid_features},
                    name=layer_name,
                    tooltip=tooltip,
                    style_function=style_fn
                ).add_to(m)
    else:
        st.warning(f"{layer_name}.geojson wurde nicht gefunden!")

# Layer-Steuerung
folium.LayerControl().add_to(m)

add_color_legend(m)

# Karte anzeigen
st_data = st_folium(m, width=800, height=600)