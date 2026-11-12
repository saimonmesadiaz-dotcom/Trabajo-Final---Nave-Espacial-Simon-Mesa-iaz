import streamlit as st

from utils.core import (
    estilos, visual, captura, estado, ejecutar,
    encabezado, guia_lateral, lista_comandos_voz
)
from utils.tema import tema

st.set_page_config(
    page_title="Puente de Mando",
    page_icon="🎙️",
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
    border:1px solid rgba(0,234,255,.4);
    background:linear-gradient(100deg,#0d1b35dd,#24123bdd);
    margin-bottom:18px;
">
    <div style="font-size:12px;letter-spacing:3px;color:#9b5cff;">
        SISTEMA DE COMUNICACIONES
    </div>
    <h1 style="margin:5px 0;color:#00eaff;">🎙️ PUENTE DE MANDO</h1>
    <p style="margin:0;color:#c3d8ec;">
        Control de la nave mediante comandos de voz
    </p>
</div>
""", unsafe_allow_html=True)

visual()

st.divider()

izquierda, derecha = st.columns([1, 1.15], gap="large")

with izquierda:
    with st.container(border=True):
        st.markdown("### 🎙️ Comunicaciones por voz")
        st.caption(
            "Pulsa HABLAR y pronuncia una orden para controlar la nave."
        )

        captura("voz", 160)

        st.divider()
        st.markdown("#### 💬 ¿Qué puedo decir?")
        lista_comandos_voz()

        st.markdown("#### ⌨️ Control manual por texto")
        st.caption("Escribe cualquiera de las órdenes anteriores y pulsa Enter.")

        def enviar_texto():
            ejecutar(st.session_state.txt)
            st.session_state.txt = ""

        st.text_input(
            "Escribe una orden",
            key="txt",
            on_change=enviar_texto,
            placeholder="Ejemplo: activar escudos"
        )

with derecha:
    with st.container(border=True):
        st.markdown("### 📡 Estado de la nave")
        estado()
