import os
os.environ["STREAMLIT_HOME"] = "/tmp"

import streamlit as st
import pandas as pd
import joblib
from geocoding import get_coordinates_from_address  # Asegurate que este archivo exista

# Cargar el modelo
@st.cache_resource
def load_model():
    return joblib.load("modelo_casita.pkl")

model = load_model()

st.title("Predicción de Precio de Propiedad")

barrio_a_grupo = {
    "Villa Devoto": "alto",
    "Villa Urquiza": "alto",
    "Colegiales": "alto",
    "Chacarita": "alto",
    "Villa General Mitre": "bajo",
    "Palermo": "muy_alto",
    "Villa Crespo": "alto",
    "Boedo": "bajo",
    "Caballito": "alto",
    "Belgrano": "muy_alto",
    "Barrio Norte": "muy_alto",
    "Balvanera": "bajo",
    "San Nicolás": "bajo",
    "Saavedra": "alto",
    "Nuñez": "muy_alto",
    "San Cristobal": "bajo",
    "Las Cañitas": "muy_alto",
    "Villa Luro": "bajo",
    "Recoleta": "muy_alto",
    "Parque Patricios": "muy_bajo",
    "Almagro": "medio",
    "Villa del Parque": "medio",
    "Paternal": "bajo",
    "Flores": "bajo",
    "Villa Pueyrredón": "alto",
    "Congreso": "bajo",
    "Mataderos": "muy_bajo",
    "Constitución": "muy_bajo",
    "Villa Lugano": "muy_bajo",
    "Villa Santa Rita": "bajo",
    "Liniers": "bajo",
    "Floresta": "muy_bajo",
    "Abasto": "bajo",
    "Coghlan": "alto",
    "San Telmo": "medio",
    "Villa Ortuzar": "alto",
    "Parque Centenario": "medio",
    "Monserrat": "bajo",
    "Once": "muy_bajo",
    "Retiro": "alto",
    "Parque Chas": "medio",
    "Centro / Microcentro": "bajo",
    "Barracas": "bajo",
    "Parque Chacabuco": "bajo",
    "Versalles": "bajo",
    "Monte Castro": "bajo",
    "Parque Avellaneda": "muy_bajo",
    "Boca": "muy_bajo",
    "Puerto Madero": "muy_alto",
    "Agronomía": "medio"
}

# Coordenadas centrales aproximadas de cada barrio (lat, lon)
barrio_centros = {
    "Villa Devoto": (-34.598, -58.510),
    "Villa Urquiza": (-34.576, -58.496),
    "Colegiales": (-34.587, -58.430),
    "Chacarita": (-34.591, -58.458),
    "Villa General Mitre": (-34.613, -58.490),
    "Palermo": (-34.581, -58.425),
    "Villa Crespo": (-34.601, -58.440),
    "Boedo": (-34.628, -58.430),
    "Caballito": (-34.615, -58.447),
    "Belgrano": (-34.563, -58.456),
    "Barrio Norte": (-34.588, -58.392),
    "Balvanera": (-34.612, -58.414),
    "San Nicolás": (-34.597, -58.378),
    "Saavedra": (-34.553, -58.475),
    "Nuñez": (-34.555, -58.462),
    "San Cristobal": (-34.620, -58.400),
    "Las Cañitas": (-34.572, -58.431),
    "Villa Luro": (-34.640, -58.510),
    "Recoleta": (-34.588, -58.392),
    "Parque Patricios": (-34.641, -58.417),
    "Almagro": (-34.615, -58.423),
    "Villa del Parque": (-34.610, -58.496),
    "Paternal": (-34.607, -58.464),
    "Flores": (-34.637, -58.465),
    "Villa Pueyrredón": (-34.566, -58.485),
    "Congreso": (-34.615, -58.415),
    "Mataderos": (-34.666, -58.513),
    "Constitución": (-34.629, -58.387),
    "Villa Lugano": (-34.700, -58.495),
    "Villa Santa Rita": (-34.639, -58.486),
    "Liniers": (-34.664, -58.507),
    "Floresta": (-34.639, -58.472),
    "Abasto": (-34.603, -58.419),
    "Coghlan": (-34.563, -58.474),
    "San Telmo": (-34.617, -58.373),
    "Villa Ortuzar": (-34.593, -58.460),
    "Parque Centenario": (-34.615, -58.443),
    "Monserrat": (-34.611, -58.383),
    "Once": (-34.608, -58.410),
    "Retiro": (-34.594, -58.370),
    "Parque Chas": (-34.577, -58.466),
    "Centro / Microcentro": (-34.608, -58.373),
    "Barracas": (-34.649, -58.380),
    "Parque Chacabuco": (-34.648, -58.466),
    "Versalles": (-34.649, -58.517),
    "Monte Castro": (-34.634, -58.493),
    "Parque Avellaneda": (-34.654, -58.496),
    "Boca": (-34.635, -58.365),
    "Puerto Madero": (-34.608, -58.360),
    "Agronomía": (-34.601, -58.460)
}

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

# Si no hay dirección o no se pudo geocodificar, usar coordenadas del barrio
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

    # Limpiar mensajes previos
    validation_msgs.empty()
    prediction_msg.empty()

    errores = []

    # Validación: superficie total >= superficie cubierta
    if Superficie_Total < Superficie_Cubierta:
        errores.append("⚠️ La superficie total no puede ser menor que la superficie cubierta.")

    # Validar coordenadas dentro del área de Gran Buenos Aires
    if not lat or not lon:
        errores.append("⚠️ No se pudo obtener coordenadas. Revisá la dirección o barrio.")
    else:
        if not (lat_min <= lat <= lat_max):
            errores.append(f"⚠️ Latitud fuera del rango para Gran Buenos Aires ({lat_min} a {lat_max}).")
        if not (lon_min <= lon <= lon_max):
            errores.append(f"⚠️ Longitud fuera del rango para Gran Buenos Aires ({lon_min} a {lon_max}).")

    # Validar rangos según tipo de propiedad
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

    # Features derivadas
    nuevos_casos["ratio_covered_total"] = nuevos_casos["SurfCov"] / (nuevos_casos["SurfTotal"] + 1e-5)
    nuevos_casos["total_rooms_surface_ratio"] = nuevos_casos["SurfTotal"] / (nuevos_casos["Rooms"] + 1)
    nuevos_casos["covered_rooms_surface_ratio"] = nuevos_casos["SurfCov"] / (nuevos_casos["Rooms"] + 1)

    pred = model.predict(nuevos_casos)
    prediction_msg.success(f"💰 Precio predicho: {pred[0]:,.2f}")
