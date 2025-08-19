import streamlit as st
import pandas as pd
import folium
import json
import geopandas as gpd
from streamlit_folium import st_folium
from pathlib import Path
from branca.colormap import StepColormap
import matplotlib.pyplot as plt
from streamlit.components.v1 import html
from branca.element import MacroElement
from jinja2 import Template

# --- Inhaltsverzeichnis ---
st.sidebar.title("Inhaltsverzeichnis")
toc_items = {
    "1. Karte": "#karte",
    "2. Durchschnittliche Belastung pro Jahr": "#durchschnitt",
    "3. Weitere Informationen zu den Datensätzen": "#informationen",
    "   3.1 NO₂-Flächenbelastung": "#info_no2_flaeche",
    "   3.2 NO₂-Straßenrandbelastung": "#info_no2_strasse",
    "   3.3 PM₁₀-Flächenbelastung": "#info_pm10_flaeche",
    "   3.4 PM₁₀-Straßenrandbelastung": "#info_pm10_strasse"
}
for name, anchor in toc_items.items():
    st.sidebar.markdown(f"- [{name}]({anchor})")

st.markdown("<a name='karte'></a>", unsafe_allow_html=True) 
st.title("1. Interaktive Karte mit Layer-Steuerung")

# GeoJSON-Verzeichnis und Dateien
geojson_dir = Path("C:/Users/benab/.vscode/extensions/Dev/Project2")
boundary_file = "dresden_grenze.geojson"
geojson_files = [f for f in geojson_dir.glob("*.geojson") if f.name != boundary_file]
layer_options = [f.stem for f in geojson_files]

col1, col2 = st.columns([5, 1])
# Layerauswahl
with col1:
    selected_layers = st.multiselect(
        "Wähle die Layer aus, die angezeigt werden sollen:",
        layer_options
    )

class MetricScaleControl(MacroElement):
    _template = Template(u"""
        {% macro script(this, kwargs) %}
        var mapObj = {{this._parent.get_name()}};
        mapObj.whenReady(function() {
            L.control.scale({
                metric: true,
                imperial: false,
                position: 'bottomleft'
            }).addTo(mapObj);
        });
        {% endmacro %}
    """)

# Karte ohne eingebauten Maßstab
m = folium.Map(location=[51.05, 13.74], zoom_start=12)

# Nur metrischen Maßstab hinzufügen
m.add_child(MetricScaleControl())

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

colors = [ "#008000", "#ADFF2F", "#FFFF00", "#FFA500","#FF0000"] 
thresholds = [0, 15, 20, 27, 40, 41]

colormap = StepColormap(
    colors=colors,
    index=thresholds,
    vmin=0, vmax=40
)
colormap.caption = "NO₂-Konzentration (µg/m³)"

# GeoJSON-Layer verarbeiten
for layer_name in selected_layers:
    filepath = geojson_dir / f"{layer_name}.geojson"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        # NO₂ Fläche
        if "no2" in layer_name and "flaeche" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["NO2", "Jahr"],
                aliases=["NO₂-Belastung (µg/m³):", "Jahr:"]
            )
            style_fn = lambda feature: {
                "fillColor": colormap(feature["properties"].get("NO2")),
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


            def style_fn(feature):
                return {
                    "color": colormap(feature["properties"].get("no2_i1")),
                    "weight": 3
                }

            # Nur Features mit gültigem Wert anzeigen
            valid_features = [
            f for f in geojson_data["features"]
            if isinstance(f["properties"].get("no2_i1"), (int, float)) and f["properties"]["no2_i1"] is not None
            ]

            if valid_features:
                folium.GeoJson(
                    data={"type": "FeatureCollection", "features": valid_features},
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
                "fillColor": colormap(feature["properties"].get("PM10")),
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
            
            
            def style_fn(feature):
                return {
                    "color": colormap(feature["properties"].get("pm10_ist")),
                    "weight": 3
                }
            valid_features = [
                f for f in geojson_data["features"]
                if isinstance(f["properties"].get("pm10_ist"), (int, float)) and f["properties"]["pm10_ist"] is not None
            ]

            if valid_features:
                folium.GeoJson(
                    data={"type": "FeatureCollection", "features": valid_features},
                    name=layer_name,
                    tooltip=tooltip,
                    style_function=style_fn
                ).add_to(m)

    else:
        st.warning(f"{layer_name}.geojson wurde nicht gefunden!")

folium.LayerControl().add_to(m)
# Daten sammeln
jahres_daten = {
    "NO2 Fläche": {},
    "NO2 Straße": {},
    "PM10 Fläche": {},
    "PM10 Straße": {}
}

for layer_name in layer_options:
    filepath = geojson_dir / f"{layer_name}.geojson"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            props = feature.get("properties", {})
            jahr = str(props.get("Jahr") or props.get("jahr") or "unbekannt")

            if "no2" in layer_name and "flaeche" in layer_name:
                val = props.get("NO2")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["NO2 Fläche"].setdefault(jahr, []).append(val)

            elif "no2" in layer_name and "strasse" in layer_name:
                val = props.get("no2_i1")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["NO2 Straße"].setdefault(jahr, []).append(val)

            elif "pm10" in layer_name and "flaeche" in layer_name:
                val = props.get("PM10")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["PM10 Fläche"].setdefault(jahr, []).append(val)

            elif "pm10" in layer_name and "strasse" in layer_name:
                val = props.get("pm10_ist")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["PM10 Straße"].setdefault(jahr, []).append(val)

# Durchschnitt pro Jahr berechnen
df = pd.DataFrame({
    name: {jahr: round(sum(vals)/len(vals), 2) for jahr, vals in jahres.items()}
    for name, jahres in jahres_daten.items()
}).sort_index()

# Diagramm zeichnen
fig, ax = plt.subplots(figsize=(10, 5))
df.plot(ax=ax, marker='o')
ax.set_ylabel("Belastung (µg/m³)")
ax.set_xlabel("Jahr")
ax.set_title("NO₂ und PM₁₀ – Durchschnittliche Jahresbelastung")
ax.grid(True)
ax.legend(title="Kategorie")


col1, col2 = st.columns([5, 1])
st.set_page_config(layout="wide")
with col1:
    st_folium(m, width=1000, height=600)
    
with col2:
    st.markdown(
        """
        <div style="
            width: 220px;
            background-color: white;
            border:2px solid grey;
            border-radius:10px;
            z-index:9999;
            font-size:14px;
            padding: 16px 16px 8px 16px;
            margin-top: 8px;
            margin-bottom: 8px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.15);
            ">
            <b>NO<sub>2</sub>- / PM<sub>10</sub>-Belastung</b><br><br>
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span style="display:inline-block; background:#FF0000; width:15px; height:15px; border-radius:3px; margin-right:10px; opacity:0.8;"></span>
                &gt; 40 µg/m³
            </div>
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span style="display:inline-block; background:#FFA500; width:15px; height:15px; border-radius:3px; margin-right:10px; opacity:0.8;"></span>
                27 - 40 µg/m³
            </div>
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span style="display:inline-block; background:#FFFF00; width:15px; height:15px; border-radius:3px; margin-right:10px; border:1px solid #eee; opacity:0.8;"></span>
                20 - 27 µg/m³
            </div>
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span style="display:inline-block; background:#ADFF2F; width:15px; height:15px; border-radius:3px; margin-right:10px; opacity:0.8;"></span>
                15 - 20 µg/m³
            </div>
            <div style="display:flex; align-items:center;">
                <span style="display:inline-block; background:#008000; width:15px; height:15px; border-radius:3px; margin-right:10px; opacity:0.8;"></span>
                ≤ 15 µg/m³
            </div>
        </div>
        """, unsafe_allow_html=True
    )
st.markdown("<a name='durchschnitt'></a>", unsafe_allow_html=True)
st.header("2. Durchschnittliche Belastung pro Jahr")
st.pyplot(fig)

# Weitere Informationen
st.markdown("<a name='informationen'></a>", unsafe_allow_html=True)
st.header("3. Weitere Informationen zu den Datensätzen")

# Unterkapitel
st.markdown("<a name='info_no2_flaeche'></a>", unsafe_allow_html=True)
st.subheader("3.1 NO₂-Flächenbelastung")
st.write("""
Die flächenhaften NO₂-Daten zeigen modellierte Jahresmittelwerte der Stickstoffdioxid-Konzentration 
in einem Raster von 1 × 1 Kilometer über das gesamte Dresdner Stadtgebiet. Grundlage ist eine Modellierung 
des Sächsischen Landesamts für Umwelt, Landwirtschaft und Geologie (LfULG), die Verkehrsstärken, Fahrmuster, 
Emissionsfaktoren, meteorologische Daten, Bebauungsstrukturen und Messwerte der ständigen Luftschadstoffüberwachung kombiniert.
""")
st.markdown("<a name='info_no2_strasse'></a>", unsafe_allow_html=True)
st.subheader("3.2 NO₂-Straßenrandbelastung")
st.write("""
Diese Datensätze enthalten modellierte NO₂-Jahresmittelwerte **direkt am Straßenrand** für ein ausgewähltes Hauptstraßennetz. 
Die Berechnungen berücksichtigen u. a. Verkehrsdichte, Fahrmuster, Straßenneigung, Bebauungshöhe und -dichte, 
sowie Aufwirbelungen und Abrieb.
""")

st.markdown("<a name='info_pm10_flaeche'></a>", unsafe_allow_html=True)
st.subheader("3.3 PM₁₀-Flächenbelastung")
st.write("""Die flächenhaften PM₁₀-Daten zeigen modellierte Jahresmittelwerte der Feinstaubkonzentration 
(Partikel mit einem aerodynamischen Durchmesser ≤ 10 µm) in einem 1 × 1 km-Raster. 
Die Modellierung nutzt ähnliche Eingangsdaten wie bei NO₂, zusätzlich werden Ferntransport-Effekte 
(z. B. Staub aus Osteuropa, Saharastaub) berücksichtigt.
""")

st.markdown("<a name='info_pm10_strasse'></a>", unsafe_allow_html=True)
st.subheader("3.4 PM₁₀-Straßenrandbelastung")
st.write("""
Diese Daten geben die modellierte PM₁₀-Belastung direkt an Hauptverkehrsstraßen wieder. 
Neben lokalen Quellen wie Verkehr und Baustellen können auch großräumige Staubtransporte den Wert beeinflussen.
""")