import requests
import streamlit as st

@st.cache_data(ttl=3600)
def get_coordinates_from_address(address):
    if not address:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'addressdetails': 0
    }

    headers = {
        "User-Agent": "MiAppCasita/1.0 (tomasesantos@hotmail.com)"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        st.warning(f"Error buscando dirección: {e}")
    
    return None, None
