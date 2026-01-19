import plotly.graph_objects as go
import pandas as pd

# 1. Luodaan KEKSITTYÄ dataa suoraan koodissa
# (Ei vaadi GEDCOMia eikä geocodingia)
fake_data = [
    # Matti Meikäläinen (Turku -> Helsinki)
    {'Name': 'Matti', 'Year': 1850, 'Lat': 60.45, 'Lon': 22.26, 'Place': 'Turku (Syntymä)'},
    {'Name': 'Matti', 'Year': 1910, 'Lat': 60.16, 'Lon': 24.93, 'Place': 'Helsinki (Kuolema)'},
    
    # Maija Meikäläinen (Oulu -> Tampere)
    {'Name': 'Maija', 'Year': 1860, 'Lat': 65.01, 'Lon': 25.46, 'Place': 'Oulu (Syntymä)'},
    {'Name': 'Maija', 'Year': 1930, 'Lat': 61.49, 'Lon': 23.78, 'Place': 'Tampere (Kuolema)'},
]

print("Luodaan testidataa...")
df = pd.DataFrame(fake_data)

fig = go.Figure()

# Piirretään viivat
for name, group in df.groupby('Name'):
    fig.add_trace(go.Scatter3d(
        x=group['Lon'], y=group['Lat'], z=group['Year'],
        mode='lines+markers',
        line=dict(width=5),
        marker=dict(size=5),
        name=name
    ))

# Asettelu
fig.update_layout(
    title='TESTIKUUTIO - Toimiiko tämä?',
    scene=dict(
        xaxis_title='Longitude (Itä-Länsi)',
        yaxis_title='Latitude (Pohjois-Etelä)',
        zaxis_title='Vuosi',
    )
)

fig.write_html('testi_tuloste.html')
print("Valmis! Avaa 'testi_tuloste.html'. Näetkö kaksi viivaa?")
