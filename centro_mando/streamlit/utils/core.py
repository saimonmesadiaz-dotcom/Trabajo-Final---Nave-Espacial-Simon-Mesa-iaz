# utils/core.py
import streamlit as st

def inicializar_estado():
    if "estado_sistema" not in st.session_state:
        st.session_state.estado_sistema = {
            "conexion_wokwi": True,
            "compuerta": "Cerrada",          # Abierta / Cerrada
            "escudos": "Desactivos",         # Activos / Desactivos
            "alerta": "Normal",              # Normal / Alerta Roja / Alerta Extrema
            "combustible": 45,               # Porcentaje simulado
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
```[cite: 11]

---

### 2. Actualización de `utils/tema.py` (Estética Espacial, Barra Lateral Azul y Efectos de Brillo)
Este módulo inyecta los estilos CSS para la barra lateral azul espacial con estrellas levitando, los efectos de brillo (*glow*) en los enlaces y los paneles de telemetría.

```python
# utils/tema.py
import streamlit as st

def aplicar_estilos_espaciales():
    st.markdown("""
        <style>
        /* Fondo general de la aplicación */
        .stApp {
            background-color: #0b0f19;
            color: #e2e8f0;
        }

        /* Barra lateral con diseño azul espacial */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #090d16 0%, #1e1b4b 100%);
            border-right: 1px solid #312e81;
        }
        
        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }

        /* Efecto brillo / hover en enlaces de la barra lateral */
        [data-testid="stSidebar"] .stMarkdown a {
            transition: all 0.3s ease;
            border-radius: 8px;
            padding: 4px 8px;
        }
        [data-testid="stSidebar"] .stMarkdown a:hover {
            background-color: rgba(59, 130, 246, 0.25);
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.7);
            color: #60a5fa !important;
        }

        /* Tarjetas de telemetría y paneles estéticos */
        .metric-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid #334155;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(4px);
        }

        /* Header fijo superior de estado con Wokwi */
        .telemetry-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background: rgba(15, 23, 42, 0.95);
            border-bottom: 1px solid #1e293b;
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header_telemetria():
    estado = st.session_state.estado_sistema
    conexion = "🟢 Conectado a Wokwi (MQTT)" if estado["conexion_wokwi"] else "🔴 Desconectado de Wokwi"
    alerta_color = "#ef4444" if estado["alerta"] != "Normal" else "#22c55e"
    
    st.markdown(f"""
        <div class="telemetry-header">
            <div><b>CENTRO DE MANDO ESPACIAL</b></div>
            <div>{conexion}</div>
            <div style="color: {alerta_color}; font-weight: bold;">ESTADO: {estado['alerta'].upper()}</div>
        </div>
    """, unsafe_allow_html=True)
```[cite: 11]

---

### 3. Actualización de `app.py` (Página Principal con Guía, Header Fijo y Alertas Sincronizadas)
Este archivo organiza la guía inicial en la barra lateral, muestra el listado de comandos y valida coherentemente las alertas en el header fijo si intentas despegar con combustible bajo.

```python
# app.py
import streamlit as st
from utils.core import inicializar_estado, procesar_comando
from utils.tema import aplicar_estilos_espaciales, render_header_telemetria

st.set_page_config(page_title="Centro de Mando - Nave Espacial", layout="wide")

# Inicializar estilos espaciales y estado
aplicar_estilos_espaciales()
inicializar_estado()

# --- BARRA LATERAL (Diseño Azul y Guía) ---
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/60a5fa/rocket.png", width=60)
    st.title("🛰️ Guía del Sistema")
    st.markdown("---")
    st.markdown("### ¿En qué consiste esta interfaz?")
    st.info(
        "Esta interfaz de control permite enviar comandos de voz o gestos simulados "
        "para interactuar en tiempo real con los subsistemas físicos simulados en **Wokwi**."
    )
    
    st.markdown("### 📋 Comandos Válidos")
    st.markdown("""
    Ejemplos de comandos admitidos:
    * `Abrir compuerta` / `Cerrar compuerta`
    * `Activar escudos` / `Desactivar escudos`
    * `Activar alerta roja` / `Normal`
    * `Iniciar despegue`
    """)
    st.markdown("---")
    st.markdown("🌟 *Ingeniería de Diseño - EAFIT*")

# --- PANTALLA PRINCIPAL ---
render_header_telemetria()

st.title("🚀 Tablero de Control y Telemetría")

# Control de entrada de comandos
col_input, col_btn = st.columns([3, 1])
with col_input:
    comando_usuario = st.text_input("Introduce comando de voz o gesto:", placeholder="Ej. Abrir compuerta...")
with col_btn:
    st.text("")
    st.text("")
    if st.button("Enviar Comando", type="primary"):
        if comando_usuario:
            procesar_comando(comando_usuario)
            st.rerun()

st.markdown("---")

# --- PANELES DE ESTADO VISUAL ---
col1, col2, col3, col4 = st.columns(4)
estado = st.session_state.estado_sistema

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <h4>🚪 Compuerta</h4>
            <h2>{estado['compuerta']}</h2>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <h4>🛡️ Escudos</h4>
            <h2>{estado['escudos']}</h2>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <h4>⛽ Combustible</h4>
            <h2>{estado['combustible']}%</h2>
        </div>
    """, unsafe_allow_html=True)

with col4:
    alerta_txt = estado['alerta']
    st.markdown(f"""
        <div class="metric-card">
            <h4>🚨 Alerta</h4>
            <h2 style="color: {'#ef4444' if alerta_txt != 'Normal' else '#22c55e'};">{alerta_txt}</h2>
        </div>
    """, unsafe_allow_html=True)

# Validación cruzada de restricciones (Coherencia en comandos vs telemetría)
if estado['combustible'] < 50 and estado['alerta'] == "Alerta Roja":
    st.error("⚠️ **Alerta de Emergencia:** Combustible bajo detectado. Para iniciar despegue debes introducir el comando de nivelación de tanques o asegurar nivel superior al 50%.")

# Visualización estética del cohete
st.markdown("### 🔭 Previsualización Visual del Cohete")
st.code("""
      /\\
     /  \\       [Estado Wokwi: Sincronizado]
    |----|      [Motores: En espera]
    | 🚀 |      [Protocolo de Seguridad: Activo]
    |____|
   //    \\\\
  """, language="text")
```[cite: 11]

---

### 4. Páginas Secundarias (`pages/Puente de Mando.py` y `pages/Sala de Maquinas.py`)
Para mantener la sincronización y el tema visual en las páginas adicionales, actualiza el inicio de cada archivo dentro de la carpeta `pages/`:

```python
# pages/Puente de Mando.py
import streamlit as st
from utils.core import inicializar_estado
from utils.tema import aplicar_estilos_espaciales, render_header_telemetria

st.set_page_config(page_title="Puente de Mando", layout="wide")
aplicar_estilos_espaciales()
inicializar_estado()
render_header_telemetria()

st.title("🕹️ Puente de Mando - Gestión de Compuertas y Escudos")
estado = st.session_state.estado_sistema

st.write(f"Estado de la compuerta en Wokwi: **{estado['compuerta']}**")
st.write(f"Estado de los escudos: **{estado['escudos']}**")

if st.button("Alternar Compuerta"):
    estado['compuerta'] = "Cerrada" if estado['compuerta'] == "Abierta" else "Abierta"
    st.rerun()
```[cite: 11]
