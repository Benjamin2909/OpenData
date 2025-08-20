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
from adjustText import adjust_text

# --- Inhaltsverzeichnis ---
st.sidebar.title("Navigation")
toc_items = {
    "1. Interaktive Karte": "#Dashboard",
    "2. Entwicklung der mittleren Luftverschmutzung": "#Durchschnitt",
    "3. Informationen zur NO₂-Belastung": "#NO₂-Informationen",
    "4. Informationen zu PM₁₀-Belastung": "#PM₁₀-Informationen",
}
for name, anchor in toc_items.items():
    st.sidebar.markdown(f"- [{name}]({anchor})")

st.markdown("<a name='Dashboard'></a>", unsafe_allow_html=True) 
st.title("1. Dashboard zur Luftverschmutzung in Dresden")

# GeoJSON-Verzeichnis und Dateien
geojson_dir = Path("Benjaminn2909/OpenData")
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
        if "NO2" in layer_name and "Flächenbelastung" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["NO2", "Jahr"],
                aliases=["NO₂-Flächenbelastung (µg/m³):", "Jahr:"]
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
        elif "NO2" in layer_name and "Straßenrandbelastung" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["no2_i1", "jahr"],
                aliases=["NO₂-Straßenrandbelastung (µg/m³):", "Jahr:"]
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
        elif "PM10" in layer_name and "Flächenbelastung" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["PM10", "Jahr"],
                aliases=["PM10-Flächenbelastung (µg/m³):", "Jahr:"]
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
        elif "PM10" in layer_name and "Straßenrandbelastung" in layer_name:
            tooltip = folium.GeoJsonTooltip(
                fields=["pm10_ist", "jahr"],
                aliases=["PM10-Straßenrandbelastung (µg/m³):", "Jahr:"]
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
    "NO2-Flächenbelastung": {},
    "NO2-Straßenrandbelastung": {},
    "PM10-Flächenbelastung": {},
    "PM10-Straßenrandbelastung": {}
}

for layer_name in layer_options:
    filepath = geojson_dir / f"{layer_name}.geojson"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data["features"]:
            props = feature.get("properties", {})
            jahr = str(props.get("Jahr") or props.get("jahr") or "unbekannt")

            if "NO2" in layer_name and "Fläche" in layer_name:
                val = props.get("NO2")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["NO2-Flächenbelastung"].setdefault(jahr, []).append(val)

            elif "NO2" in layer_name and "Straße" in layer_name:
                val = props.get("no2_i1")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["NO2-Straßenrandbelastung"].setdefault(jahr, []).append(val)

            elif "PM10" in layer_name and "Fläche" in layer_name:
                val = props.get("PM10")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["PM10-Flächenbelastung"].setdefault(jahr, []).append(val)

            elif "PM10" in layer_name and "Straße" in layer_name:
                val = props.get("pm10_ist")
                if isinstance(val, (int, float)) and val > 0:
                    jahres_daten["PM10-Straßenrandbelastung"].setdefault(jahr, []).append(val)

# Durchschnitt pro Jahr berechnen
df = pd.DataFrame({
    name: {jahr: round(sum(vals)/len(vals), 2) for jahr, vals in jahres.items()}
    for name, jahres in jahres_daten.items()
}).sort_index()

def _sort_key(idx):
    out = []
    for x in idx:
        s = str(x)
        out.append(int(s) if s.isdigit() else 10**9)  # Nicht-Zahlen ganz ans Ende
    return out

df = df.sort_index(key=_sort_key).round(2)
df.index = df.index.astype(int)
df.index.name = "Jahr"  # nur kosmetisch für die Achsenbeschriftung

# Diagramm zeichnen
fig, ax = plt.subplots(figsize=(10, 5))
df.plot(ax=ax, marker='o')
plt.ylim(bottom=10,top=40)
texts=[]
for col in df.columns:
    for x, y in zip(df.index, df[col]):
        texts.append(ax.text(x, y+0.3, f"{y:.2f}", ha="center", va="bottom", fontsize=8))
adjust_text(texts, ax=ax)
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
st.markdown("<a name='Durchschnitt'></a>", unsafe_allow_html=True)
st.header("2. Entwicklung der mittleren Luftverschmutzung")
col1, col2 = st.columns([5, 1])
with col1:
    st.pyplot(fig)

# Unterkapitel
st.markdown("<a name='NO₂-Informationen'></a>", unsafe_allow_html=True)
st.subheader("3. Informationen zur NO₂-Belastung")
st.write("""**1. Problemstellung**\n
Einer der gesundheitlich relevanten Luftschadstoffe, bei denen die Einhaltung der Grenzwerte in der Vergangenheit nicht überall gelang, ist Stickstoffdioxid. Seit 2010 gelten in der Europäischen Union zwei Grenzwerte:\n    
- der Jahresmittelwert von 40 Mikrogramm pro Kubikmeter (μg/m³) und
- der Stundenmittelwert von 200 μg/m³, welcher 18-mal im Jahr überschritten werden darf.\n
In Dresden wird das Kriterium für den Stundenmittelwert überall sicher eingehalten. Es gibt aber Straßenabschnitte an vielbefahrenen Hauptstraßen, an denen der Jahresmittelwert über 40 μg/m³ liegt.
In der Europäischen Union hat man sich auf einen neuen Jahresmittel-Grenzwert von 20 μg/m³ geeinigt, der bis zum Jahr 2030 zu erreichen ist. Dieser Wert ist 2024 in Kraft getreten. Von der Weltgesundheitsorganisation (WHO) wird ein Jahresgrenzwert von 10 μg/m³ vorgeschlagen.
Quellen der Stickoxidbelastung sind Verbrennungsvorgänge. Überall dort, wo Energie aus fossilen Brennstoffen oder auch aus nachwachsendem biologischem Material durch Verbrennung gewonnen wird, entstehen Stickoxide. Dabei ist in Dresden der Kraftfahrzeugverkehr die größte Einzelquelle.
Zur Verifizierung des Luftreinhalteplanes für die Landeshauptstadt Dresden aus dem Jahr 2017 wurden modellbasierte Analysen durchgeführt.\n
**2. Datengrundlage**\n
Um zu stadtweiten, vergleichbaren Aussagen zu kommen, wurde die NO2-Belastung für Dresden vom Sächsischen Landesamt für Umwelt, Landwirtschaft und Geologie (LfULG) modelliert. Die Ergebnisse liegen
- einmal als flächenhafte Schadstoffbelastung in einem Ein-Kilometer-Raster und\n
- als Straßenrandbelastung auf einem ausgewählten Hauptstraßennetz der Landeshauptstadt Dresden vor.\n
Folgende Daten gingen in die Modellierung ein:\n
- Verkehrsstärken (Zählungen des Straßen- und Tiefbauamtes der Stadt Dresden, aufbereitet durch das Umweltamt, Stand 2017),\n
- Fahrmuster zur Beschreibung des Verkehrsflusses (Ermittlung durch den Lehrstuhl für Verkehrsökologie der Technischen Universität Dresden im Auftrag des LfULG),\n
- Emissionsfaktoren der Kraftfahrzeuge (HBEFA 3.3) mit Korrekturen des LfULG,\n
- Emissionsdaten für Aufwirbelungen durch den Kraftfahrzeugverkehr und Abrieb von Bremsbelägen, Kupplungen, Reifen und Straßenoberflächen, die auf Arbeiten des Ingenieurbüros Lohmeyer GmbH & Co. KG beruhen und ähnlich den dem Handbuch für Emissionsfaktoren (HBEFA) bestimmten Verkehrssituationen zugeordnet wurden,\n
- Neigung der Straßenabschnitte (Umweltamt),\n
- Bebauungsdaten, wie durchschnittliche Höhe, durchschnittlicher Abstand und durchschnittliche Dichte der Bebauung an dem jeweiligen Straßenabschnitt, die auf Grundlage der digitalen Stadtkarte ermittelt wurden (Umweltamt),\n
- Meteorologische Ausbreitungsbedingungen (Windstatistik Großer Garten, DWD),\n
- Messdaten der ständigen Luftschadstoffüberwachung des LfULG der drei Dresdner Stationen.\n
Stickstoffdioxid ist kein inertes Gas, das heißt, es reagiert schnell mit anderen Luftschadstoffkomponenten wie Stickstoffmonoxid, Ozon etc. Das muss bei den Berechnungen berücksichtigt werden.\n
Die Daten der flächenhaften Belastung wurden zur Darstellung mit Hilfe eines GIS-Systems „über das Stadtgebiet gelegt“. Die Daten zur Straßenrandbelastung wurden zur Darstellung auf das Straßenknotennetz der Stadt Dresden (ESKN 25) mit Hilfe einer Schlüsselbrücke übertragen.\n
**3. Methode**\n
Das LfULG berechnet auf der Grundlage des Sächsischen Emissionskatasters und der Daten der Landeshauptstadt Dresden sowohl die flächenhafte Belastung, wie auch die Straßenrandbelastung mit Hilfe des Programmsystems Immikart, das das Ingenieurbüro Lohmeyer GmbH & Co. KG für das LfULG entwickelt hat. Das Programmsystem beinhaltet sowohl ein Modul für die flächenhafte Belastung als auch ein Modul für die direkte Straßenrandbelastung in bebauten Gebieten (Prokas B). Als Maß für die Güte der Berechnungen dient dabei die erreichte Übereinstimmung mit den gemessenen Luftgütewerten.\n
**4. Kartenbeschreibung**\n
Die Karte stellt vor einem Stadthintergrund, der zur besseren Orientierung im Stadtgebiet dient, im Ein-Kilometer-Raster die flächenhafte NO2-Belastung als Jahresmittelwert dar. Zusätzlich wird die häufig erhöhte Luftverschmutzung am Straßenrand für ein speziell festgelegtes Straßennetz der Stadt Dresden dargestellt. Beide Werte zusammen können einen Eindruck über die Belastungssituation in der Stadt vermitteln. Punktgenaue Aussagen sind naturgemäß in einem Ein-Kilometer-Raster nicht möglich. Auch bei der berechneten Straßenrandbelastung sind derartige Aussagen nicht möglich, weil die verwendeten Bebauungsdaten (Fahrbahnabstand, Bebauungsdichte, Bebauungshöhe), die zur Ermittlung dieser Belastung herangezogen werden, Mittelwerte sind, die für mindestens 65 Meter lange Abschnitte gelten.\n
""")

st.markdown("<a name='PM₁₀-Informationen'></a>", unsafe_allow_html=True)
st.subheader("4. Informationen zur PM₁₀-Belastung")
st.write("""**1. Problemstellung**\n
Einer der gesundheitlich relevanten Luftschadstoffe, bei de-nen die Einhaltung der Grenzwerte in der Vergangenheit nicht überall gelang, ist die Staubbelastung. Dabei wird seit 2002 nicht mehr der Gesamtstaub betrachtet, sondern nur die Teilchen mit einem aerodynamischen Durchmesser von circa zehn Mikrometer (1 Mikrometer = 0,000001 Meter). Die Bezeichnung „PM10“ wird aus dem Englischen „particulate matter“ abgeleitet. Die „10“ steht für die zehn Mikrometer (μm) des Teilchendurchmessers.\n
Seit 2005 gelten in der Europäischen Union zwei Grenzwerte:\n
- der Jahresmittelwert von 40 Mikrogramm pro Kubikmeter (μg/m³) und\n
- der Tagesmittelwert von 50 μg/m³, welcher 35-mal im Jahr überschritten werden darf.\n
Es gibt einen statistischen Zusammenhang zwischen der Anzahl der Überschreitungen des Grenzwertes für Tagesmittel und dem Jahresmittelwert. Ab einem Jahresmittelwert von 29 μg/m³ muss mit mehr als den zulässigen 35 Überschreitungen des Grenzwertes für das Tagesmittel von 50 μg/m³ gerechnet werden. Die Wahrscheinlichkeit der Nichteinhaltung des Tagesmittelwertkriteriums steigt mit der Höhe des Jahresmittelwertes.
In Dresden wird der aktuelle Jahresmittelwert überall sicher eingehalten. Es gibt aber Straßenabschnitte an vielbefahrenen Hauptstraßen, an denen PM10-Belastungen über 29 μg/m³ im Jahresmittel auftreten. Hier sind dann mehr als 35 Überschreitungen des Tagesmittelwertes möglich.
In der Europäischen Union hat man sich auf einen neuen Jahresmittel-Grenzwert von 20 μg/m³ geeinigt, der bis zum Jahr 2030 zu erreichen ist. Dieser Wert wird ab 2024 in Kraft treten. Von der Weltgesundheitsorganisation (WHO) wird ein Grenzwert von 15 μg/m³ vorgeschlagen.
Quellen der PM10-Belastung sind alle menschlichen Aktivitäten (Verkehr, Industrie, Haushalte, Handwerk usw.), wobei in Dresden der Kraftfahrzeugverkehr die größte Einzelquelle ist. Hinzu kommen natürliche Quellen (Meersalz, Wüstenstaub, Vulkanausbrüche, Verwehungen von feinen Boden-bestandteilen usw.). Ein Phänomen, das Dresden besonders betrifft, sind dabei Ferntransporte aus östlicher und südlicher Richtung. Sind solche Wetterlagen noch mit Inversionswetterlagen verknüpft, müssen in Dresden oft Grenzwertüberschreitungen festgestellt werden, die nicht mit städtischen Maßnahmen verhindert werden können.
Zur Verifizierung des Luftreinhalteplanes für die Landeshauptstadt Dresden aus dem Jahr 2017 wurden modellbasierte Analysen durchgeführt.\n
**2. Datengrundlage**\n
Um zu stadtweiten, vergleichbaren Aussagen zu kommen, wurde die PM10-Belastung für Dresden vom Sächsischen Landesamt für Umwelt, Landwirtschaft und Geologie (LfULG) modelliert. Die Ergebnisse liegen\n
- einmal als flächenhafte Schadstoffbelastung in einem Ein-Kilometer-Raster und\n
- als Straßenrandbelastung auf einem ausgewählten Hauptstraßennetz der Landeshauptstadt Dresden vor.\n
Folgende Daten gingen in die Modellierung ein:\n
- Verkehrsstärken (Zählungen des Straßen- und Tiefbauamtes der Stadt Dresden, aufbereitet durch das Umweltamt, Stand 2017),\n
- Fahrmuster zur Beschreibung des Verkehrsflusses (Ermittlung durch den Lehrstuhl für Verkehrsökologie der Technischen Universität Dresden im Auftrag des LfULG),\n
- Emissionsfaktoren der Kraftfahrzeuge (HBEFA 3.3) mit Korrekturen des LfULG,\n
- Emissionsdaten für Aufwirbelungen durch den Kraftfahrzeugverkehr und Abrieb von Bremsbelägen, Kupplungen, Reifen und Straßenoberflächen, die auf Arbeiten des Ingenieurbüros Lohmeyer GmbH & Co. KG beruhen und ähnlich den dem Handbuch für Emissionsfaktoren (HBEFA) bestimmten Verkehrssituationen zugeordnet wurden,\n
- Neigung der Straßenabschnitte (Umweltamt),\n
- Bebauungsdaten, wie durchschnittliche Höhe, durchschnittlicher Abstand und durchschnittliche Dichte der Bebauung an dem jeweiligen Straßenabschnitt, die auf Grundlage der digitalen Stadtkarte ermittelt wurden (Umweltamt),\n
- Meteorologische Ausbreitungsbedingungen (Windstatistik Großer Garten, DWD),\n
- Messdaten der ständigen Luftschadstoffüberwachung des LfULG der drei Dresdner Stationen.\n
Die Daten der flächenhaften Belastung wurden zur Darstellung mit Hilfe eines GIS-Systems „über das Stadtgebiet gelegt“. Die Daten zur Straßenrandbelastung wurden zur Darstellung auf das Straßenknotennetz der Stadt Dresden (ESKN 25) mit Hilfe einer Schlüsselbrücke übertragen.\n
**3. Methode**\n
Das LfULG berechnet auf der Grundlage des Sächsischen Emissionskatasters und der Daten der Landeshauptstadt Dresden sowohl die flächenhafte Belastung, wie auch die Straßenrandbelastung mit Hilfe des Programmsystems Immikart, das das Ingenieurbüro Lohmeyer GmbH & Co. KG für das LfULG entwickelt hat. Das Programmsystem beinhaltet sowohl ein Modul für die flächenhafte Belastung als auch ein Modul für die direkte Straßenrandbelastung in bebauten Gebieten (Prokas B). Als Maß für die Güte der Berechnungen dient dabei die erreichte Übereinstimmung mit den gemessenen Werten.\n
**4. Kartenbeschreibung**\n
Die Karte stellt vor einem Stadthintergrund, der zur besseren Orientierung im Stadtgebiet dient, im Ein-Kilometer-Raster die flächenhafte PM10-Belastung als Jahresmittelwert dar. Zusätzlich wird die häufig erhöhte Luftverschmutzung am Straßenrand für ein speziell festgelegtes Straßennetz der Stadt Dresden dargestellt. Beide Werte zusammen können einen Eindruck über die Belastungssituation in der Stadt vermitteln. Punktgenaue Aussagen sind naturgemäß in einem Ein-Kilometer-Raster nicht möglich. Auch bei der berechneten Straßenrandbelastung sind derartige Aussagen nicht möglich, weil die verwendeten Bebauungsdaten (Fahrbahnabstand, Bebauungsdichte, Bebauungshöhe), die zur Ermittlung dieser Belastung herangezogen werden, Mittelwerte sind, die für mindestens 65 Meter lange Abschnitte gelten.\n
""")

