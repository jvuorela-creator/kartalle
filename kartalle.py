import sys
import os
import re
from midiutil import MIDIFile

# --- ASETUKSET (MUOKKAA NÄITÄ) ---
GEDCOM_FILE = 'sukupuu.ged'   # Varmista että tämä tiedosto on samassa kansiossa!
OUTPUT_FILE = 'sukusinfonia.mid'

# Tempo ja kesto
TEMPO = 120
BEATS_PER_YEAR = 0.5  # 1 vuosi = puoli iskua

# Soittimet (General MIDI)
# 40=Viulu, 42=Sello, 73=Huilu, 0=Piano
INSTRUMENT_HIGH = 40 
INSTRUMENT_LOW = 42  

# --- YKSINKERTAINEN PARSERI ---
# Tehty ilman ulkoisia kirjastoja virheiden välttämiseksi

def parse_year(date_str):
    """Etsii vuosiluvun tekstistä."""
    if not date_str: return None
    match = re.search(r'\d{4}', date_str)
    if match: return int(match.group(0))
    return None

def get_panning(place_name):
    """Arpoo panoroinnin paikan nimen perusteella (yksinkertaistettu)."""
    if not place_name: return 64
    p = place_name.lower()
    # Vasen (Länsi)
    if any(x in p for x in ['turku', 'åbo', 'pori', 'vaasa', 'helsinki', 'espoo']): return 30
    # Oikea (Itä)
    if any(x in p for x in ['viipuri', 'joensuu', 'kuopio', 'karjala', 'sortavala']): return 100
    return 64

def simple_gedcom_reader(filename):
    """Lukee GEDCOMin rivi riviltä ja etsii syntymät/kuolemat."""
    events = []
    
    if not os.path.exists(filename):
        print(f"VIRHE: Tiedostoa '{filename}' ei löydy!")
        return []

    print(f"Luetaan tiedostoa: {filename}...")
    
    current_id = None
    current_evt = None # 'BIRT' tai 'DEAT'
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        print(f"Tiedosto luettu. Rivejä yhteensä: {len(lines)}")
        
        for line in lines:
            line = line.strip()
            parts = line.split(' ', 2)
            if len(parts) < 2: continue
            
            level = parts[0]
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else ""

            # 1. Uusi henkilö
            if level == '0' and value == 'INDI': # Joskus ID on tagin paikalla, tämä on yksinkertaistus
                continue 
            if level == '0' and tag.startswith('@') and value == 'INDI':
                current_id = tag
                current_evt = None
                
            # 2. Tapahtuman tunnistus
            elif level == '1':
                if tag == 'BIRT': current_evt = 'BIRT'
                elif tag == 'DEAT': current_evt = 'DEAT'
                else: current_evt = None
                
            # 3. Päivämäärä
            elif level == '2' and tag == 'DATE' and current_evt:
                year = parse_year(value)
                if year:
                    events.append({
                        'year': year,
                        'type': 'BIRTH' if current_evt == 'BIRT' else 'DEATH',
                        'place': '' # Paikka haetaan seuraavaksi jos löytyy
                    })

            # 4. Paikka (
