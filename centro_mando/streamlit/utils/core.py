# utils/core.py
import streamlit as st

def inicializar_estado():
    if "estado_sistema" not in st.session_state:
        st.session_state.estado_sistema = {
            "conexion_wokwi": True,
            "compuerta": "Cerrada",          # Abierta / Cerrada
            "escudos": "Desactivos",         # Activos / Desactivos
            "alerta": "Normal",              # Normal / Alerta Roja / Alerta Extrema
            "combustible": 45,               # Porcentaje simulado bajo para prueba
            "comandos_validos": [
                "Abrir compuerta", "Cerrar compuerta",
                "Activar escudos", "Desactivar escudos",
                "Activar alerta roja", "Normal", "Iniciar despegue"
            ]
        }

def procesar_comando(comando: str):
    cmd = comando.lower().strip()
    st.session_state.ultimo_comando = comando
    
    if "abrir compuerta" in cmd:
        st.session_state.estado_sistema["compuerta"] = "Abierta"
    elif "cerrar compuerta" in cmd:
        st.session_state.estado_sistema["compuerta"] = "Cerrada"
    elif "activar escudos" in cmd:
        st.session_state.estado_sistema["escudos"] = "Activos"
    elif "desactivar escudos" in cmd:
        st.session_state.estado_sistema["escudos"] = "Desactivos"
    elif "alerta roja" in cmd:
        st.session_state.estado_sistema["alerta"] = "Alerta Roja"
    elif "normal" in cmd:
        st.session_state.estado_sistema["alerta"] = "Normal"
    elif "iniciar despegue" in cmd:
        if st.session_state.estado_sistema["combustible"] < 50:
            st.session_state.estado_sistema["alerta"] = "Alerta Roja"
        else:
            st.success("🚀 Despegue autorizado y sincronizado con Wokwi.")
