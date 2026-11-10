import streamlit as st
st.set_page_config(page_title="Centro de Mando Galáctico", page_icon="🚀", layout="wide")
from utils.core import estilos, nucleo, barra_lateral, visual

nucleo(); estilos(); barra_lateral()
st.title("🚀 CENTRO DE MANDO GALÁCTICO")
st.write("Simulación de robótica y astronomía con control sin contacto. **Puente de Mando:** voz. **Sala de Máquinas:** gestos. Sube la temperatura a más de 30 °C en Wokwi y se acercan los meteoritos.")
visual("ventana")
