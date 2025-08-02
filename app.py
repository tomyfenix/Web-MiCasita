import os
os.environ["STREAMLIT_HOME"] = "/tmp"

from huggingface_hub import hf_hub_download
import streamlit as st
import pandas as pd
import joblib
from geocoding import get_coordinates_from_address  # Asegurate que este archivo exista

# Cargar el modelo desde Hugging Face si no existe localmente
MODEL_REPO = "tu_usuario/tu_repo"  # Reemplaza con tu usuario y repo
MODEL_FILENAME = "modelo_casita.pkl"
LOCAL_MODEL_PATH = MODEL_FILENAME

if not os.path.exists(LOCAL_MODEL_PATH):
    st.write("Descargando modelo desde Hugging Face Hub...")
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILENAME, local_dir=".", local_dir_use_symlinks=False)

@st.cache_resource
def load_model():
    return joblib.load(LOCAL_MODEL_PATH)

model = load_model()

st.title("Predicción de Precio de Propiedad")

# ---
# Agregás aquí todos los diccionarios barrio_a_grupo y barrio_centros exactamente como los tenías.
# ---

# Limites geográficos para Gran Buenos Aires (aproximados)
lat_min, lat_max = -35.2, -34.3
lon_min, lon_max = -59.3, -57.9

# Inputs del usuario
Habitaciones = st.number_input("Cantidad de habitaciones", min_value=1, value=1)
Baños = st.number_input("Cantidad de baños", min_value=1, value=1)
Superficie_Total = st.number_input("Superficie total (m2)", min_value=1.0, value=44.0)
Superficie_Cubierta = st.number_input("Superficie cubierta (m2)", min_value=1.0, value=38.0)
direccion = st.text_input("Dirección (ej: 'Av. Santa Fe 1200, CABA') o deje vacío para evaluar por barrio unicamente")
Tipo_de_Propiedad = st.selectbox("Tipo de propiedad", ["Departamento", "Casa", "PH"])
barrio = st.selectbox("Barrio", sorted(barrio_a_grupo.keys()))
parrilla = st.checkbox("¿Tiene parrilla?")
cochera = st.checkbox("¿Tiene cochera o garage?")
lavadero = st.checkbox("¿Tiene lavadero?")
terraza = st.checkbox("¿Tiene terraza?")
suite = st.checkbox("¿Tiene suite?")

# Contenedores para mensajes
coords_msg = st.empty()
validation_msgs = st.empty()
prediction_msg = st.empty()

# Obtener coordenadas automáticamente
lat, lon = get_coordinates_from_address(direccion)

if direccion.strip() == "" or lat is None or lon is None:
    lat, lon = barrio_centros.get(barrio, (None, None))
    if lat and lon:
        coords_msg.info(f"📍 Usando coordenadas centrales del barrio {barrio}: {lat:.5f}, {lon:.5f}")
    else:
        coords_msg.warning("No se encontró coordenadas para el barrio seleccionado.")
else:
    coords_msg.info(f"📍 Coordenadas: {lat:.5f}, {lon:.5f}")

grupo_precio = barrio_a_grupo.get(barrio, "medio")

if st.button("Predecir precio"):
    validation_msgs.empty()
    prediction_msg.empty()
    errores = []

    if Superficie_Total < Superficie_Cubierta:
        errores.append("⚠️ La superficie total no puede ser menor que la superficie cubierta.")

    if not lat or not lon:
        errores.append("⚠️ No se pudo obtener coordenadas. Revisá la dirección o barrio.")
    else:
        if not (lat_min <= lat <= lat_max):
            errores.append(f"⚠️ Latitud fuera del rango para Gran Buenos Aires ({lat_min} a {lat_max}).")
        if not (lon_min <= lon <= lon_max):
            errores.append(f"⚠️ Longitud fuera del rango para Gran Buenos Aires ({lon_min} a {lon_max}).")

    if Tipo_de_Propiedad == "Casa":
        if not (2 <= Habitaciones <= 7):
            errores.append("⚠️ Casas: habitaciones deben estar entre 2 y 7.")
        if not (50 <= Superficie_Total <= 560):
            errores.append("⚠️ Casas: superficie total debe estar entre 50 y 560 m2.")
        if not (1 <= Baños <= 4):
            errores.append("⚠️ Casas: baños deben estar entre 1 y 4.")
    elif Tipo_de_Propiedad == "Departamento":
        if not (1 <= Habitaciones <= 4):
            errores.append("⚠️ Departamentos: habitaciones deben estar entre 1 y 4.")
        if not (30 <= Superficie_Total <= 140):
            errores.append("⚠️ Departamentos: superficie total debe estar entre 30 y 140 m2.")
        if not (1 <= Baños <= 3):
            errores.append("⚠️ Departamentos: baños deben estar entre 1 y 3.")
    elif Tipo_de_Propiedad == "PH":
        if not (2 <= Habitaciones <= 5):
            errores.append("⚠️ PH: habitaciones deben estar entre 2 y 5.")
        if not (30 <= Superficie_Total <= 260):
            errores.append("⚠️ PH: superficie total debe estar entre 30 y 260 m2.")
        if not (1 <= Baños <= 3):
            errores.append("⚠️ PH: baños deben estar entre 1 y 3.")

    if errores:
        validation_msgs.warning("\n".join(errores))
        st.stop()

    nuevos_casos = pd.DataFrame({
        'Rooms': [Habitaciones],
        'Baths': [Baños],
        'SurfTotal': [Superficie_Total],
        'SurfCov': [Superficie_Cubierta],
        'Lat': [lat],
        'Lon': [lon],
        'PropType': [Tipo_de_Propiedad],
        'Grupo_Precio': [grupo_precio],
        'Parrilla': [parrilla],
        'Cochera/Garage': [cochera],
        'Lavadero': [lavadero],
        'Terraza': [terraza],
        'Suite': [suite]
    })

    nuevos_casos["ratio_covered_total"] = nuevos_casos["SurfCov"] / (nuevos_casos["SurfTotal"] + 1e-5)
    nuevos_casos["total_rooms_surface_ratio"] = nuevos_casos["SurfTotal"] / (nuevos_casos["Rooms"] + 1)
    nuevos_casos["covered_rooms_surface_ratio"] = nuevos_casos["SurfCov"] / (nuevos_casos["Rooms"] + 1)

    pred = model.predict(nuevos_casos)
    prediction_msg.success(f"💰 Precio predicho: {pred[0]:,.2f}")
