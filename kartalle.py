import sys
import os
import re
from midiutil import MIDIFile

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged' 
OUTPUT_FILE = 'sukusinfonia.mid'

def get_panning(place):
    # Yksinkertainen logiikka ilman sisäkkäisiä luuppeja
    if not place: return 64
    txt = place.lower()
    if 'turku' in txt or 'pori' in txt or 'helsinki' in txt: return 30
    if 'viipuri' in txt or 'joensuu' in txt or 'karjala' in txt: return 100
    return 64

def main():
    # 1. Tarkistus
    if not os.path.exists(GEDCOM_FILE):
        print("VIRHE: Tiedostoa ei loydy.")
        return

    # 2. Luku (Ei try-lohkoa sisennyksen valttamiseksi)
    events = []
    with open(GEDCOM_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    current_type = None
    
    for line in lines:
        parts = line.strip().split(' ', 2)
        if len(parts) < 2: continue
        
        level = parts[0]
        tag = parts[1]
        val = parts[2] if len(parts) > 2 else ""

        if level == '0':
            current_type = None
        
        if level == '1' and (tag == 'BIRT' or tag == 'DEAT'):
            current_type = tag
            
        if level == '2' and tag == 'DATE' and current_type:
            # Etsi vuosi
            m = re.search(r'\d{4}', val)
            if m:
                year = int(m.group(0))
                events.append({'y': year, 't': current_type, 'p': ''})
                
        if level == '2' and tag == 'PLAC' and current_type and len(events) > 0:
            events[-1]['p'] = val

    # 3. MIDI
    if len(events) == 0:
        print("Ei tapahtumia.")
        return

    events.sort(key=lambda x: x['y'])
    start_year = events[0]['y']
    
    midi = MIDIFile(1)
    midi.addTrackName(0, 0, "Sukusinfonia")
    midi.addTempo(0, 0, 120)
    midi.addProgramChange(0, 0, 0, 40) # Viulu
    midi.addProgramChange(0, 1, 0, 42) # Sello

    print("Luodaan tiedostoa...")

    for e in events:
        beat = (e['y'] - start_year) * 0.5
        
        if e['t'] == 'BIRT':
            ch = 0
            note = 84
            dur = 0.5
            vol = 90
        else:
            ch = 1
            note = 36
            dur = 3.0
            vol = 60
            
        pan = get_panning(e['p'])
        midi.addControllerEvent(0, ch, beat, 10, pan)
        midi.addNote(0, ch, note, beat, dur, vol)

    with open(OUTPUT_FILE, "wb") as f:
        midi.writeFile(f)
        
    print("VALMIS.")

if __name__ == '__main__':
    main()
