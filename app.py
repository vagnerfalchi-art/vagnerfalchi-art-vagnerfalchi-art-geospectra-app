import streamlit as st
import ee
import geemap.foliumap as geemap
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim

# Configuração de Interface Profissional (Layer 2)
st.set_page_config(layout="wide", page_title="GEOSPECTRA V1.60 FINAL")

# --- L1: OS 14 MINERAIS ---
db_mineral = {
    'Ouro (Nativo/Sufetos)': {'b': ('B11', 'B2'), 'lim': 2.15},
    'Lítio (Pegmatitos)': {'b': ('B11', 'B8'), 'lim': 1.70},
    'Esmeralda/Berilo': {'b': ('B3', 'B2'), 'lim': 1.55},
    'Terras Raras (REE)': {'b': ('B11', 'B12'), 'lim': 1.95},
    'Nióbio (Carbonatitos)': {'b': ('B12', 'B4'), 'lim': 2.25},
    'Alexandrita': {'b': ('B8', 'B4'), 'lim': 2.50},
    'Cobre (Porfirítico)': {'b': ('B12', 'B8A'), 'lim': 2.10},
    'Níquel (Laterítico)': {'b': ('B8A', 'B11'), 'lim': 1.65},
    'Ferro (Hematita)': {'b': ('B4', 'B2'), 'lim': 1.95},
    'Diamante Vermelho (Host)': {'b': ('B12', 'B2'), 'lim': 2.65},
    'Manganês': {'b': ('B11', 'B4'), 'lim': 2.15},
    'Tântalo/Coltã': {'b': ('B12', 'B11'), 'lim': 1.80},
    'Ródio (PGM)': {'b': ('B11', 'B8'), 'lim': 1.95},
    'Platina/Paládio': {'b': ('B12', 'B8'), 'lim': 1.85}
}

st.sidebar.title("💎 GEOSPECTRA V1.60")
cidade = st.sidebar.text_input('🏙️ Localidade:', 'Canaã dos Carajás, PA')
mineral = st.sidebar.selectbox('💎 Selecione o Mineral:', sorted(list(db_mineral.keys())))
sensib = st.sidebar.slider('🎚️ Sensibilidade Espectral:', 0.01, 4.0, 1.21, 0.01)

if st.sidebar.button("🚀 EXECUTAR VARREDURA"):
    try:
        ee.Initialize()
        loc = Nominatim(user_agent="geos_app_v160").geocode(cidade)
        if loc:
            ponto = ee.Geometry.Point([loc.longitude, loc.latitude])
            area = ponto.buffer(10000).bounds()
            
            # Engine L4 (Sentinel-2)
            s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(area).sort('system:time_start', False).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).first().clip(area)
            scan_date = datetime.fromtimestamp(s2.get('system:time_start').getInfo()/1000.0).strftime('%d/%m/%Y')
            
            m = db_mineral[mineral]
            ratio = s2.select(m['b'][0]).divide(s2.select(m['b'][1])).rename('val')
            mask = ratio.gt(sensib).And(s2.normalizedDifference(['B8', 'B4']).lt(0.45))
            alvos_img = ratio.updateMask(mask)
            
            st.metric("Alvos Detectados em", scan_date)
            
            # Mapa Estável
            Map = geemap.Map(center=[loc.latitude, loc.longitude], zoom=13)
            Map.add_basemap('HYBRID')
            Map.addLayer(s2, {'bands':['B12','B8','B4'], 'max':3500}, 'Satélite')
            Map.addLayer(alvos_img, {'min':sensib, 'max':sensib+0.5, 'palette':['blue','yellow','red']}, 'Detecção Mineral')
            Map.to_streamlit(height=700)
        else:
            st.error("Local não encontrado.")
    except Exception as e:
        st.error(f"Erro no motor: {e}")
