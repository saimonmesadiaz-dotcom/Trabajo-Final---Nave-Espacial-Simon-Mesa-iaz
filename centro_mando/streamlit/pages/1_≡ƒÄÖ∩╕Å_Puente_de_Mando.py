import streamlit as st
from utils.core import estilos, visual, captura, estado, ejecutar
st.set_page_config(page_title="Puente de Mando", page_icon="🎙️", layout="wide")
estilos(); st.title("🎙️ PUENTE DE MANDO · VOZ")
visual()
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Micrófono")
    st.caption("Pulsa HABLAR y di: activar escudos · abrir compuerta · cerrar compuerta · alerta roja · iniciar despegue · abortar misión")
    captura("voz", 160)
    def enviar_texto():
        ejecutar(st.session_state.txt); st.session_state.txt = ""
    st.text_input("Plan B: escribe el comando", key="txt", on_change=enviar_texto)
with c2: estado()
