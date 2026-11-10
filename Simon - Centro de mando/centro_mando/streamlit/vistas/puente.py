import streamlit as st
from utils.core import visual, captura, estado, ejecutar
st.title("🎙️ PUENTE DE MANDO · VISOR Y VOZ")
visual("ventana")
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Micrófono")
    st.caption("Di: activar escudos · abrir compuerta · cerrar compuerta · alerta roja · iniciar despegue · abortar misión")
    captura("voz", 160)
    def enviar_texto():
        ejecutar(st.session_state.txt); st.session_state.txt = ""
    st.text_input("Plan B: escribe el comando", key="txt", on_change=enviar_texto)
with c2: estado()
