import sys
import re
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from midiutil import MIDIFile

# --- ASETUKSET ---
GEDCOM_FILE = 'sukupuu.ged'  # VAIHDA TÄMÄN TILALLE OMA TIEDOSTOSI
ROOT_ID = '@I500003@'             # VAIHDA TÄMÄ ITSEESI (PROBANDIIN)
OUTPUT_FILE = 'sukusinfonia.mid'

# Aikaskaala: Kuinka nopeasti vuodet kuluvat?
# 0.25 iskua per vuosi tarkoittaa, että 100 vuotta kestää n. 25 iskua (nopea).
BEATS_PER_YEAR = 0.5 
TEMPO = 120  # BPM

# Soittimet (General MIDI numerot)
# 40 = Viulu, 42 = Sello, 0 = Piano (varalla)
INSTRUMENT_FATHER = 42 # Sello
INSTRUMENT_MOTHER = 40 # Viulu
INSTRUMENT_UNKNOWN = 0 # Piano

# Nuotit
NOTE_BIRTH = 84  # C6 (Korkea)
NOTE_DEATH = 36  # C2 (Matala)

# --- APUFUNKTIOT ---

def parse_year(date_str):
    """Etsii vuosiluvun GEDCOM-päivämäärästä (esim. '12 MAY 1860' -> 1860)."""
    if not date_str: return None
    match = re.search(r'\d{4}', date_str)
    if match:
        return int(match.group(0))
    return None

def get_panning(place_name):
    """
    Arvaa sijainnin perusteella panoroinnin (Länsi-Itä).
    0 = Vasen (Länsi), 64 = Keski, 127 = Oikea (Itä).
    Tämä on yksinkertaistettu lista esimerkin vuoksi.
    """
    if not place_name: return 64
    place = place_name.lower()
    
    # Länsi-Suomi / Rannikko (Vasen)
    west = ['turku', 'åbo', 'pori', 'vaasa', 'helsinki', 'espoo', 'rauma', 'ahvenanmaa']
    # Itä-Suomi / Karjala (Oikea)
    east = ['joensuu', 'kuopio', 'viipuri', 'sortavala', 'kajaani', 'lappeenranta', 'savonlinna']
    
    for w in west:
        if w in place: return 30  # Selkeästi vasemmalla
    for e in east:
        if e in place: return 100 # Selkeästi oikealla
        
    return 64 # Oletus keskellä

def analyze_lineage(gedcom_parser, root_id):
    """
    Käy läpi sukupuun ja lajittelee esi-isät isän ja äidin puolelle.
    Palauttaa kaksi settiä ID-tunnuksia: fathers_side, mothers_side.
    """
    fathers_side = set()
    mothers_side = set()
    
    root_person = gedcom_parser.get_element_dictionary().get(root_id)
    if not root_person:
        print("Virhe: Juurihenkilöä ei löydy.")
        return set(), set()

    # Haetaan vanhemmat
    parents = gedcom_parser.get_parents(root_person)
    father = None
    mother = None
    
    for p in parents:
        if p.get_gender() == 'M': father = p
        if p.get_gender() == 'F': mother = p
        
    # Rekursiivinen haku
    def add_ancestors(person, side_set):
        if not person: return
        side_set.add(person.get_pointer())
        for parent in gedcom_parser.get_parents(person):
            add_ancestors(parent, side_set)

    if father:
        print(f"Isän haara alkaa: {father.get_name()[0]} {father.get_name()[1]}")
        add_ancestors(father, fathers_side)
    if mother:
        print(f"Äidin haara alkaa: {mother.get_name()[0]} {mother.get_name()[1]}")
        add_ancestors(mother, mothers_side)
        
    return fathers_side, mothers_side

# --- PÄÄOHJELMA ---

def main():
    print(f"Luetaan tiedostoa {GEDCOM_FILE}...")
    gedcom = Parser()
    try:
        gedcom.parse_file(GEDCOM_FILE)
    except FileNotFoundError:
        print("Virhe: Tiedostoa ei löydy. Tarkista nimi.")
        return

    print("Analysoidaan sukuhaaroja...")
    fathers_side, mothers_side = analyze_lineage(gedcom, ROOT_ID)
    
    events = [] # (Vuosi, Tyyppi, Sukuhaara, Paikka)

    print("Kerätään tapahtumia...")
    elements = gedcom.get_element_list()
    for element in elements:
        if isinstance(element, IndividualElement):
            person_id = element.get_pointer()
            
            # Määritä haara
            lineage = 'UNKNOWN'
            if person_id in fathers_side: lineage = 'FATHER'
            elif person_id in mothers_side: lineage = 'MOTHER'
            elif person_id == ROOT_ID: lineage = 'ROOT'
            else: continue # Ohitetaan sisarukset/serkut, jos halutaan vain suorat esivanhemmat
            
            # Syntymä
            birth = element.get_birth_data()
            birth_year = parse_year(birth[0])
            if birth_year:
                place = birth[1]
                events.append({'year': birth_year, 'type': 'BIRTH', 'lineage': lineage, 'place': place})
            
            # Kuolema
            death = element.get_death_data()
            death_year = parse_year(death[0])
            if death_year:
                place = death[1]
                events.append({'year': death_year, 'type': 'DEATH', 'lineage': lineage, 'place': place})

    # Järjestetään aikajärjestykseen
    events.sort(key=lambda x: x['year'])
    
    if not events:
        print("Ei tapahtumia löytynyt. Tarkista GEDCOM.")
        return

    min_year = events[0]['year']
    max_year = events[-1]['year']
    print(f"Aikajana: {min_year} - {max_year} ({len(events)} tapahtumaa)")

    # --- MIDI LUONTI ---
    midi = MIDIFile(2) # Kaksi raitaa (0=Isä/Sello, 1=Äiti/Viulu)
    
    # Raita 0: Sello (Isä)
    midi.addTrackName(0, 0, "Isän suku")
    midi.addTempo(0, 0, TEMPO)
    midi.addProgramChange(0, 0, 0, INSTRUMENT_FATHER) 
    
    # Raita 1: Viulu (Äiti)
    midi.addTrackName(1, 0, "Äidin suku")
    midi.addTempo(1, 0, TEMPO)
    midi.addProgramChange(1, 1, 0, INSTRUMENT_MOTHER) # Channel 1

    for event in events:
        # Ajoitus
        time = (event['year'] - min_year) * BEATS_PER_YEAR
        
        # Sukuhaara määrittää raidan ja kanavan
        if event['lineage'] == 'FATHER':
            track = 0; channel = 0
        elif event['lineage'] == 'MOTHER':
            track = 1; channel = 1
        else:
            track = 0; channel = 0 # Root menee oletuksena raidalle 0
            
        # Nuotti ja kesto
        if event['type'] == 'BIRTH':
            pitch = NOTE_BIRTH
            duration = 0.5 # Lyhyt "ping"
            velocity = 100 # Voimakas
        else: # DEATH
            pitch = NOTE_DEATH
            duration = 4.0 # Pitkä sointi
            velocity = 70 # Hiljaisempi
            
        # Panorointi (Sijainti)
        pan_value = get_panning(event['place'])
        # MIDI Control Change 10 = Pan
        midi.addControllerEvent(track, channel, time, 10, pan_value)
        
        # Lisää nuotti
        midi.addNote(track, channel, pitch, time, duration, velocity)

    # Tallennus
    with open(OUTPUT_FILE, "wb") as output_file:
        midi.writeFile(output_file)
        
    print(f"Valmis! Tallennettu: {OUTPUT_FILE}")
    print("Avaa tiedosto musiikkiohjelmassa (GarageBand, Logic, MuseScore) kuullaksesi äänet oikein.")

if __name__ == '__main__':
    main()
