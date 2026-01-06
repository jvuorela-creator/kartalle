import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import pandas as pd

# --- ASETUKSET ---
st.set_page_config(page_title="Sukututkijan Karttapalvelu", layout="wide")

# --- APUFUNKTIOT ---

def parse_gedcom_simple(file_content):
    """
    Yksinkertainen GEDCOM-jäsennin, joka etsii henkilöt ja syntymäpaikat.
    Tämä on tehty kestäväksi, jotta se ei kaadu erikoisiin merkistöihin.
    """
    people = []
    current_person = None
    lines = file_content.split('\n')
    
    for line in lines:
        line = line.strip()
        parts = line.split(' ', 2)
        
        if len(parts) < 2:
            continue
            
        level = parts[0]
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ""
        
        # Uusi henkilö alkaa
        if level == '0' and value.endswith('INDI'):
            if current_person and 'name' in current_person:
                people.append(current_person)
            current_person = {'id': parts[1], 'events': {}}
            
        # Nimi
        elif level == '1' and tag == 'NAME' and current_person is not None:
            current_person['name'] = value.replace('/', '') # Siivotaan kauttaviivat
            
        # Syntymäpaikka (yksinkertaistettu logiikka: etsii 1 BIRT -> 2 PLAC)
        elif level == '1' and tag == 'BIRT' and current_person is not None:
            current_person['last_tag'] = 'BIRT'
        elif level == '2' and tag == 'PLAC' and current_person is not None:
            if current_person.get('last_tag') == 'BIRT':
                current_person['birth_place'] = value
                
    # Lisätään viimeinenkin listaan
    if current_person and 'name' in current_person:
        people.append(current_person)
        
    return people

@st.cache_data
def geocode_locations(locations):
    """
    Hakee koordinaatit paikkakunnille. Käyttää välimuistia (cache), 
    jotta hakuja ei tehdä turhaan uudestaan.
    """
    geolocator = Nominatim(user_agent="genealogy_mapper_v1")
    results = {}
    
    # Progress bar käyttöliittymään
    progress_bar = st.progress(0)
    total = len(locations)
    
    for i, place in enumerate(locations):
        # Päivitetään progress bar
        progress_bar.progress((i + 1) / total)
        
        if place in results:
            continue
            
        try:
            # HUOM: Tähän voisi lisätä sanakirjan historiallisille paikoille
            # Esim: if place == "Wiborg": search_place = "Vyborg"
            
            location = geolocator.geocode(place)
            if location:
                results[place] = (location.latitude, location.longitude)
            else:
                results[place] = None
            
            # Ollaan kohteliaita API:lle (Nomimatim vaatii 1s viiveen)
            time.sleep(1.1)
            
        except (GeocoderTimedOut, Exception):
            results[place] = None
            
    progress_bar.empty()
    return results

# --- KÄYTTÖLIITTYMÄ ---

st.title("🗺️ Sukututkijan Muuttoliikekartta")
st.markdown("""
Lataa **GEDCOM-tiedostosi** (.ged), niin sovellus piirtää esivanhempiesi syntymäpaikat kartalle.
*Huom: Tämä on demoversio. Historialliset paikannimet (esim. vanhat pitäjät) eivät välttämättä löydy automaattisesti nykykartoista.*
""")

uploaded_file = st.file_uploader("Valitse GEDCOM-tiedosto", type=['ged'])

if uploaded_file is not None:
    # Luetaan tiedosto
    string_data = uploaded_file.getvalue().decode("utf-8", errors='ignore')
    
    st.info("Tiedosto ladattu. Analysoidaan rakennetta...")
    
    # 1. Parsitaan data
    people = parse_gedcom_simple(string_data)
    
    # Suodatetaan vain ne, joilla on syntymäpaikka
    people_with_places = [p for p in people if 'birth_place' in p]
    
    st.write(f"Löydettiin {len(people)} henkilöä, joista {len(people_with_places)}:lla on merkitty syntymäpaikka.")
    
    if len(people_with_places) > 0:
        # Kerätään uniikit paikat geokoodausta varten
        unique_places = list(set([p['birth_place'] for p in people_with_places]))
        
        st.write(f"Haetaan koordinaatteja {len(unique_places)} eri paikkakunnalle...")
        
        # 2. Geokoodataan
        coords = geocode_locations(unique_places)
        
        # 3. Piirretään kartta
        m = folium.Map(location=[64.0, 26.0], zoom_start=5)
        
        found_count = 0
        missing_count = 0
        
        for p in people_with_places:
            place = p['birth_place']
            latlon = coords.get(place)
            
            if latlon:
                folium.Marker(
                    location=latlon,
                    popup=f"<b>{p['name']}</b><br>Syntyi: {place}",
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(m)
                found_count += 1
            else:
                missing_count += 1
        
        st_folium(m, width=800, height=500)
        
        st.success(f"Kartta valmis! {found_count} henkilöä sijoitettu kartalle.")
        if missing_count > 0:
            st.warning(f"{missing_count} henkilön paikkaa ei löytynyt karttapalvelusta (todennäköisesti vanha/muuttunut nimi).")
            
        # Näytetään data taulukkona debuggausta varten
        if st.checkbox("Näytä löydetty data taulukkona"):
            df = pd.DataFrame(people_with_places)
            st.dataframe(df)