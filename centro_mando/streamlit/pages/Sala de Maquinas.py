import streamlit as st

from utils.core import (
    estilos, visual, captura, estado, enviar,
    encabezado, guia_lateral, lista_gestos
)
from utils.tema import tema

st.set_page_config(
    page_title="Sala de Máquinas",
    page_icon="🖐️",
    layout="wide"
)

estilos()
tema()
guia_lateral()
encabezado()

st.markdown("""
<div style="
    padding:18px 22px;
    border-radius:16px;
    border:1px solid rgba(155,92,255,.5);
    background:linear-gradient(100deg,#111b39dd,#25123bdd);
    margin-bottom:18px;
">
    <div style="font-size:12px;letter-spacing:3px;color:#ff35d3;">
        SISTEMA DE PROPULSIÓN Y CONTROL
    </div>
    <h1 style="margin:5px 0;color:#00eaff;">🖐️ SALA DE MÁQUINAS</h1>
    <p style="margin:0;color:#c3d8ec;">
        Control de sistemas mediante gestos y comandos manuales
    </p>
</div>
""", unsafe_allow_html=True)

visual()

st.divider()

izquierda, derecha = st.columns([1, 1.15], gap="large")

with izquierda:
    with st.container(border=True):
        st.markdown("### 🖐️ Reconocimiento de gestos")
        st.caption(
            "Utiliza la cámara para enviar órdenes a la nave."
        )

        captura("gest", 480)

        lista_gestos()

    with st.expander("🛠️ Modo manual de respaldo"):
        st.markdown("#### Potencia de motores")

        st.slider(
            "Motores %",
            0,
            100,
            0,
            25,
            key="mot",
            on_change=lambda: enviar(motores=st.session_state.mot)
        )

        b1, b2, b3, b4 = st.columns(4)

        if b1.button("🛡️ Escudos", use_container_width=True):
            enviar(escudos=True)

        if b2.button("🚪 Abrir", use_container_width=True):
            enviar(compuerta=90)

        if b3.button("🚪 Cerrar", use_container_width=True):
            enviar(compuerta=0)

        if b4.button("🚀 Despegar", use_container_width=True):
            enviar(despegue=True)

with derecha:
    with st.container(border=True):
        st.markdown("### 📡 Estado de la nave")
        estado()
