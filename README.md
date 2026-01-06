# Sukututkijan Muuttoliikekartta

Tämä on Python-sovellus sukututkijoille. Se lukee GEDCOM-tiedoston, poimii henkilöiden syntymäpaikat ja visualisoi ne interaktiiviselle kartalle.

Sovellus on suunniteltu erityisesti opetuskäyttöön ja sukututkimuksen havainnollistamiseen.

## Ominaisuudet
- 📂 **GEDCOM-tuki:** Lukee standardinmukaisia sukututkimustiedostoja.
- 🌍 **Geokoodaus:** Muuttaa paikkakuntien nimet (esim. "Turku") koordinaateiksi automaattisesti.
- 🗺️ **Interaktiivinen kartta:** Zoomattava ja klikkailtava kartta (perustuu OpenStreetMapiin).

## Kuinka käyttää
1. Mene sovelluksen osoitteeseen (linkki Streamlit Cloudiin).
2. Lataa `.ged` tiedosto koneeltasi.
3. Odota hetki, kun sovellus hakee koordinaatit.
4. Tutki karttaa.

## Huomioitavaa datasta
Sovellus käyttää `Nominatim`-palvelua paikannukseen. Se löytää hyvin nykyiset paikkakunnat. Vanhat historialliset nimet (esim. luovutetun Karjalan pitäjät vanhoilla nimillä) eivät välttämättä löydy ilman nimen nykyaikaistamista GEDCOM-tiedostossa.

## Tekninen toteutus
Rakennettu Pythonilla käyttäen:
- `streamlit` (Käyttöliittymä)
- `folium` (Kartat)
- `geopy` (Koordinaattihaku)
