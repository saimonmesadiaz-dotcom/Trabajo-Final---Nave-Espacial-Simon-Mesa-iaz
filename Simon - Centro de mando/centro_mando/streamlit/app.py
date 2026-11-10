import streamlit as st
st.set_page_config(page_title="Centro de Mando Galáctico", page_icon="🚀", layout="wide")
from utils.core import estilos, nucleo, barra_lateral

nucleo(); estilos()
pg = st.navigation([
    st.Page("vistas/inicio.py", title="Inicio", icon="🚀", default=True),
    st.Page("vistas/puente.py", title="Puente de Mando", icon="🎙️"),
    st.Page("vistas/maquinas.py", title="Sala de Máquinas", icon="🖐️"),
])
barra_lateral()
pg.run()
