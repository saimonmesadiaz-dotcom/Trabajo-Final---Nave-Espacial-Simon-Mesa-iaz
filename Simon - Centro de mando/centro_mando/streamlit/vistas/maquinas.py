import streamlit as st
from utils.core import visual, captura, estado, enviar
st.title("🖐️ SALA DE MÁQUINAS · GESTOS")
visual("maquinas")
c1, c2 = st.columns(2)
with c1:
    captura("gestos", 480)
    st.caption("👍 escudos · 🤘 despegar · 🖐 compuerta · ✊ motores 0 % · 1-4 dedos = 25-100 %")
    with st.expander("Modo manual de respaldo"):
        st.slider("Motores %", 0, 100, 0, 25, key="mot", on_change=lambda: enviar(motores=st.session_state.mot))
        b1, b2, b3 = st.columns(3)
        if b1.button("Escudos ON"): enviar(escudos=True)
        if b2.button("Compuerta"): enviar(compuerta=90)
        if b3.button("Despegar"): enviar(despegue=True)
with c2: estado()
