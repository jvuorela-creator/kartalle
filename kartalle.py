import sys
import os
import re
from midiutil import MIDIFile

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged' 
OUTPUT_FILE = 'sukusinfonia.mid'
TEMPO = 120
BEATS_PER_YEAR = 0.5

# --- PARSERI ---
def parse_year(date_str):
    if not date_str: return None
    match = re.search(r'\d{4}', date_str)
    if match: return int(match.group(0))
    return None

def get_panning(place_name):
    if not place_name: return 64
    p = place_name.lower()
    if any(x in p for x in ['turku', 'pori', 'vaasa', 'helsinki', 'espoo']): return 30
    if any(x in p for x in ['viipuri', 'joensuu', 'kuopio', 'karjala']): return 100
    return 64

# --- PÄÄOHJELMA ---
def main():
    # 1. TARKISTETAAN TIEDOSTO
    if not os.path.exists(GEDCOM_FILE):
        print(f"VIRHE: Tiedostoa '{GEDCOM_FILE}' ei löydy.")
        return

    print(f"Luetaan tiedostoa {GEDCOM_FILE}...")

    # 2. LUETAAN DATA
    events = []
    try:
        with open(GEDCOM_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        current_evt = None
        
        for line in lines:
            parts = line.strip().split(' ', 2)
            if len(parts) < 2: continue
            
            level, tag = parts[0], parts[1]
            value = parts[2] if len(parts) > 2 else ""

            if level == '0':
                current_evt = None
            elif level == '1' and tag in ['BIRT', 'DEAT']:
                current_evt = tag
            elif level == '2' and tag == 'DATE' and current_evt:
                y = parse_year(value)
                if y:
                    events.append({'year': y, 'type': current_evt, 'place': ''})
            elif level == '2' and tag == 'PLAC' and current_evt and events:
                events[-1]['place'] = value

    except Exception as e:
        print(f"Virhe luvussa: {e}")
        return

    if not events:
        print("Ei tapahtumia löytynyt.")
        return

    events.sort(key=lambda x: x['year'])
    min_year = events[0]['year']
    
    # Tässä oli aiemmin virheen aiheuttanut kohta. Nyt se on korjattu.
    print(f"Tapahtumia: {len(events)}")
    print("Luodaan MIDI
