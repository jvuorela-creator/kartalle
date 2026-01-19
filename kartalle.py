import sys
import os
import re
from midiutil import MIDIFile

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged'   # Varmista, että tiedostonimi on oikein!
OUTPUT_FILE = 'sukusinfonia.mid'

# Tempo ja kesto
TEMPO = 120
BEATS_PER_YEAR = 0.5  # Pienempi luku = nopeampi kappale

# Soittimet (General MIDI numerot)
# 40=Viulu, 42=Sello, 0=Piano
INSTRUMENT_HIGH = 40 
INSTRUMENT_LOW = 42  

# --- APUFUNKTIOT ---

def parse_year(date_str):
    """Etsii vuosiluvun tekstistä."""
    if not date_str: return None
    match = re.search(r'\d{4}', date_str)
    if match: return int(match.group(0))
    return None

def get_panning(place_name):
    """Arpoo panoroinnin (Länsi-Itä) paikan nimen perusteella."""
    if not place_name: return 64
    p = place_name.lower()
    
    # Länsi-Suomi (Vasen kuuloke -> arvo < 64)
    west = ['turku', 'åbo', 'pori', 'vaasa', 'helsinki', 'espoo', 'rauma', 'tampere']
    for w in west:
        if w in p: return 30 
        
    # Itä-Suomi / Karjala (Oikea kuuloke -> arvo > 64)
    east = ['viipuri', 'joensuu', 'kuopio', 'karjala', 'sortavala', 'savonlinna', 'kajaani']
    for e in east:
        if e in p: return 100
        
    return 64 # Keskellä

def read_gedcom_events(filename):
    """Lukee GEDCOM-tiedoston yksinkertaistetusti."""
    events = []
    
    if not os.path.exists(filename):
        print(f"VIRHE: Tiedostoa '{filename}' ei löydy nykyisestä kansiosta.")
        print(f"Nykyinen kansio on: {os.getcwd()}")
        return []

    print(f"Luetaan tiedostoa: {filename}...")
    
    # Luetaan tiedosto rivi riviltä muistiin
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Virhe tiedoston avaamisessa: {e}")
        return []

    print(f"Rivejä luettu: {len(lines)}")
    
    current_evt = None # 'BIRT' tai 'DEAT'
    
    for line in lines:
        line = line.strip()
        parts = line.split(' ', 2)
        
        if len(parts) < 2: continue
        
        level = parts[0]
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ""

        # Kun uusi henkilö alkaa (INDI), nollataan tilanne
        if level == '0':
            current_evt = None

        # Tapahtuman tunnistus (Syntymä/Kuolema)
        elif level == '1':
            if tag == 'BIRT': 
                current_evt = 'BIRT'
            elif tag == 'DEAT': 
                current_evt = 'DEAT'
            else:
                current_evt = None
            
        # Päivämäärä (DATE)
        elif level == '2' and tag == 'DATE' and current_evt:
            year = parse_year(value)
            if year:
                events.append({
                    'year': year,
                    'type': 'BIRTH' if current_evt == 'BIRT' else 'DEATH',
                    'place': ''
                })

        # Paikka (PLAC)
        elif level == '2' and tag == 'PLAC' and current_evt and events:
            # Lisätään paikka listan viimeisimpään tapahtumaan
            events[-1]['place'] = value

    return events

# --- PÄÄOHJELMA ---

def main():
    # 1. Lue data
    events = read_gedcom_events(GEDCOM_FILE)
    
    if not events:
        print("Ei tapahtumia tai tiedostoa ei löytynyt.")
        return

    # Järjestä vuosiluvun mukaan
    events.sort(key=lambda x: x['year'])
    
    min_year = events[0]['year']
    max_year = events[-1]['year']
    print(f"Aikajana: {min_year} - {max_year}. Tapahtumia: {len(events)}")

    # 2. Luo MIDI-tiedosto
    print("Sävelletään sinfoniaa...")
    midi =
