import sys
import time
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged'  # VAIHDA TÄMÄ OMAAN TIEDOSTOON
MAX_PEOPLE = 40  # Montako henkilöä käsitellään testivaiheessa? (Rajoita aluksi, geocoding on hidasta)
USER_AGENT = "genealogy_visualizer_v1" # Tunniste geocoding-palvelulle

# Alustetaan geocoder ja GEDCOM-parseri
geolocator = Nominatim(user_agent=USER_AGENT)
gedcom_parser = Parser()
try:
    gedcom_parser.parse_file(GEDCOM_FILE)
    print(f"Luettu tiedosto: {GEDCOM_FILE}")
except FileNotFoundError:
    print(f"VIRHE: Tiedostoa '{GEDCOM_FILE}' ei löydy. Tarkista nimi.")
    sys.exit()

# Välimuisti koordinaateille, ettei samaa paikkaa haeta turhaan uudestaan
location_cache = {}

def get_lat_lon(place_name):
    """Hakee paikannimelle koordinaatit (Lat, Lon)."""
    if not place_name:
        return None
    
    # Siivotaan paikannimeä (otetaan esim. maan nimi talteen jos tarkempaa ei löydy)
    clean_place = place_name.strip()
    
    if clean_place in location_cache:
        return location_cache[clean_place]

    try:
        print(f"Haetaan koordinaatteja: {clean_place}...")
        location = geolocator.geocode(clean_place)
        time.sleep(1.1)  # TÄRKEÄ: Nominatim vaatii 1 sekunnin tauon hakujen välillä
        
        if location:
            coords = (location.latitude, location.longitude)
            location_cache[clean_place] = coords
            return coords
        else:
            print(f" -> Ei löytynyt: {clean_place}")
            return None
    except (GeocoderTimedOut, Exception) as e:
        print(f" -> Virhe haussa: {e}")
        return None

def extract_year(date_str):
    """Yksinkertainen vuoden erottelu päivämäärästä."""
    if not date_str: return None
    # Etsitään 4 numeroa stringistä
    import re
    match = re.search(r'\d{4}', date_str)
    if match:
        return int(match.group(0))
    return None

# --- DATAN KERÄYS ---
data_points = []
individuals = [e for e in gedcom_parser.get_root_child_elements() if isinstance(e, IndividualElement)]

print(f"Löydetty {len(individuals)} henkilöä. Käsitellään ensimmäiset {MAX_PEOPLE}...")

count = 0
for element in individuals:
    if count >= MAX_PEOPLE:
        break

    name = " ".join(element.get_name())
    birth = element.get_birth_data()
    death = element.get_death_data()
    
    birth_year = extract_year(birth[0])
    birth_place = birth[1]
    
    death_year = extract_year(death[0])
    death_place = death[1]

    # Otetaan mukaan vain jos on edes syntymäaika ja -paikka tiedossa
    if birth_year and birth_place:
        coords_b = get_lat_lon(birth_place)
        
        if coords_b:
            # Lisätään syntymäpiste
            data_points.append({
                'Name': name,
                'Type': 'Birth',
                'Year': birth_year,
                'Lat': coords_b[0],
                'Lon': coords_b[1],
                'Place': birth_place
            })
            
            # Jos kuolintiedot löytyvät, lisätään kuolema ja viiva niiden välille
            if death_year and death_place:
                coords_d = get_lat_lon(death_place)
                if coords_d:
                    data_points.append({
                        'Name': name,
                        'Type': 'Death',
                        'Year': death_year,
                        'Lat': coords_d[0],
                        'Lon': coords_d[1],
                        'Place': death_place
                    })
            count += 1

# --- VISUALISOINTI (PLOTLY) ---
df = pd.DataFrame(data_points)

if df.empty:
    print("Ei dataa visualisoitavaksi. Tarkista GEDCOM-tiedoston paikkamerkinnät.")
    sys.exit()

fig = go.Figure()

# 1. Piirretään viivat (elämänkaaret)
# Ryhmitellään nimen mukaan, jotta voidaan piirtää viiva syntymästä kuolemaan
for name, group in df.groupby('Name'):
    if len(group) > 1: # Tarvitaan vähintään 2 pistettä viivaan
        group = group.sort_values('Year') # Varmistetaan aikajärjestys
        fig.add_trace(go.Scatter3d(
            x=group['Lon'], y=group['Lat'], z=group['Year'],
            mode='lines',
            line=dict(width=4),
            opacity=0.6,
            name=name,
            showlegend=False
        ))

# 2. Piirretään pisteet (tapahtumat)
fig.add_trace(go.Scatter3d(
    x=df['Lon'], y=df['Lat'], z=df['Year'],
    mode='markers',
    marker=dict(
        size=5,
        color=df['Year'], # Väri vuoden mukaan
        colorscale='Viridis',
        opacity=0.8
    ),
    text=df['Name'] + " (" + df['Place'] + ")", # Hover-teksti
    name='Tapahtumat'
))

# 3. Asettelu
fig.update_layout(
    title='Suvun Aika-Paikka-Kuutio',
    scene=dict(
        xaxis_title='Pituusaste (Longitude)',
        yaxis_title='Leveysaste (Latitude)',
        zaxis_title='Vuosi (Aika)',
    ),
    margin=dict(l=0, r=0, b=0, t=50)
)

print("Valmis! Avataan selain...")
fig.show()

