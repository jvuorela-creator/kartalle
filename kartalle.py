import sys
import time
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement

# --- ASETUKSET ---
GEDCOM_FILE = 'sinun_tiedosto.ged'  # <--- TARKISTA ETTÄ TÄMÄ ON OIKEIN!
OUTPUT_FILE = 'sukupuu_kartta.html'
MAX_PEOPLE_TO_CHECK = 10  # Montako henkilöä yritetään käsitellä
USER_AGENT = "genealogy_visualizer_debug_v2"

print("--- ALOITETAAN OHJELMA ---")

# 1. Alustetaan geocoder
geolocator = Nominatim(user_agent=USER_AGENT, timeout=10)
location_cache = {}

# 2. Luetaan GEDCOM
print(f"Luetaan tiedostoa: {GEDCOM_FILE}...")
gedcom_parser = Parser()
try:
    gedcom_parser.parse_file(GEDCOM_FILE)
    print("Tiedoston luku onnistui.")
except FileNotFoundError:
    print(f"VIRHE: Tiedostoa '{GEDCOM_FILE}' ei löydy kansiosta.")
    print("Varmista, että tiedostonimi on kirjoitu koodiin täsmälleen oikein.")
    sys.exit()
except Exception as e:
    print(f"VIRHE tiedoston luvussa: {e}")
    sys.exit()

def get_lat_lon(place_name):
    """Hakee koordinaatit ja tulostaa mitä tekee."""
    if not place_name:
        return None
    
    clean_place = place_name.strip()
    
    # Tarkistetaan välimuisti
    if clean_place in location_cache:
        return location_cache[clean_place]

    try:
        print(f"   -> Haetaan koordinaatteja: '{clean_place}'...", end=" ")
        # Pieni viive ettei palvelu estä meitä
        time.sleep(1.2) 
        location = geolocator.geocode(clean_place)
        
        if location:
            print(f"OK ({location.latitude:.2f}, {location.longitude:.2f})")
            coords = (location.latitude, location.longitude)
            location_cache[clean_place] = coords
            return coords
        else:
            print("EI LÖYTYNYT")
            return None
    except Exception as e:
        print(f"VIRHE: {e}")
        return None

def extract_year(date_str):
    if not date_str: return None
    import re
    match = re.search(r'\d{4}', date_str)
    if match:
        return int(match.group(0))
    return None

# 3. Käydään läpi henkilöt
print("Etsitään henkilöitä...")
individuals = [e for e in gedcom_parser.get_root_child_elements() if isinstance(e, IndividualElement)]
print(f"Tiedostosta löytyi yhteensä {len(individuals)} henkilömerkintää.")
print(f"Käsitellään ensimmäiset {MAX_PEOPLE_TO_CHECK} henkilöä, joilla on tietoja...")

data_points = []
processed_count = 0
