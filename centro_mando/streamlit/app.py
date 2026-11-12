import streamlit as st

from utils.core import (
    estilos, visual, nucleo, encabezado, guia_lateral,
    lista_comandos_voz, lista_gestos
)
from utils.tema import tema

st.set_page_config(
    page_title="Centro de Mando Galáctico",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

estilos()
tema()
nucleo()
guia_lateral()
encabezado()

st.markdown("""
<div style="
    padding: 24px 28px;
    border: 1px solid rgba(0,234,255,.45);
    border-radius: 18px;
    background: linear-gradient(
        110deg,
        rgba(0,234,255,.10),
        rgba(155,92,255,.13),
        rgba(255,53,211,.08)
    );
    box-shadow: 0 0 25px rgba(0,234,255,.09);
    margin-bottom: 20px;
">
    <div style="
        color:#00eaff;
        font-size:12px;
        letter-spacing:4px;
        font-weight:bold;
    ">
        SISTEMA DE NAVEGACIÓN · 2026
    </div>
    <h1 style="
        font-size:32px;
        margin:8px 0;
        color:#e5faff;
        text-shadow:0 0 15px #00eaff66;
    ">
        🚀 CENTRO DE MANDO GALÁCTICO
    </h1>
    <p style="color:#b5cbe2;margin:0;">
        Centro de control de la nave · Telemetría · Voz · Gestos · Seguridad
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### ✦ ESTADO DE LA MISIÓN")

st.write(
    "Administra los sistemas de la nave desde el menú lateral. "
    "Usa el **Puente de Mando** para las órdenes por voz y la "
    "**Sala de Máquinas** para los gestos y el modo manual. "
    "El encabezado fijo te dice si hay conexión con Wokwi y te avisa "
    "cuando una orden no se puede cumplir."
)

visual()

st.divider()

c1, c2 = st.columns(2, gap="large")

with c1:
    st.markdown("### 🎙️ Comandos de voz")
    lista_comandos_voz()

with c2:
    st.markdown("### 🖐️ Gestos")
    lista_gestos()
