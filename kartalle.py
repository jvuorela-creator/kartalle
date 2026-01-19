import sys
import os
import re

# 1. TARKISTETAAN KIRJASTO HETI
try:
    from midiutil import MIDIFile
except ImportError:
    print("VIRHE: MidiUtil-kirjastoa ei löydy.")
    print("Suorita komento: pip install MidiUtil")
    sys.exit(1)

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged' 
OUTPUT_FILE = 'sukusinfonia.mid'
TEMPO = 120
BEATS_PER_YEAR = 0.5 

def parse_year(date_str):
    if not date_str: return None
    match = re.search(r'\d{4}', date_str)
    if match: return int(match.group(0))
    return None

def get_panning(place_name):
    if not place_name: return 64
    p = place_name.lower()
    # Länsi
    if any(x in p for x in ['turku', 'pori', 'vaasa', 'helsinki', 'espoo', 'tampere']): return 30
    # Itä
    if any(x in p for x in ['viipuri', 'joensuu', 'kuopio', 'karjala', 'sortavala']): return 100
    return 64

def main():
    # 2. TARKISTETAAN TIEDOSTO
    if not os.path.exists(GEDCOM_FILE):
        print(f"VIRHE: Tiedostoa '{GEDCOM_FILE}' ei löydy tästä kansiosta.")
        return

    print(f"Luetaan tiedostoa {GEDCOM_FILE}...")

    # 3. PARSETAAN DATA
    events = []
    try:
        with
