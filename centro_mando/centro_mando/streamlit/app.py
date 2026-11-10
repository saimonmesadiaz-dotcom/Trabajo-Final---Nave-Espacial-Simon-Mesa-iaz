import streamlit as st
from utils.core import estilos, visual, nucleo
st.set_page_config(page_title="Centro de Mando Galáctico", page_icon="🚀", layout="wide")
estilos(); nucleo()
st.title("🚀 CENTRO DE MANDO GALÁCTICO")
st.write("Simulación de robótica y astronomía con control sin contacto: **voz** en el Puente de Mando y **gestos** en la Sala de Máquinas. Sube la temperatura a más de 30 °C en Wokwi y se acercan los meteoritos.")
visual()
