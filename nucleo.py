
import json
import time
import uuid
import queue
import unicodedata
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import paho.mqtt.client as mqtt


# ==========================================
# CONFIGURACION GENERAL
# ==========================================

P = "NaveEspacial2026"

BROKER = "broker.hivemq.com"
PORT = 1883

TOP_ENTRADA = f"{P}/entrada"
TOP_COMANDOS = f"{P}/comandos"
TOP_TELEMETRIA = f"{P}/telemetria"

WEB = Path(__file__).resolve().parents[2] / "web"


# ==========================================
# NORMALIZAR TEXTO
# ==========================================

def normalizar(texto):

    texto = str(texto).lower().strip()

    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


# ==========================================
# INTERPRETAR VOZ
# ==========================================

def interpretar(texto):

    t = normalizar(texto)

    off = any(
        palabra in t
        for palabra in (
            "desactivar", "desactiv",
            "apagar", "apag",
            "cerrar", "cerr"
        )
    )

    if "abort" in t:
        return {"despegue": False}, "Misión abortada"

    if "despeg" in t:
        return {"despegue": True}, "Verificando despegue"

    if "escudo" in t:
        return (
            {"escudos": not off},
            "Escudos " + ("desactivados" if off else "activados")
        )

    if "alerta" in t:
        return (
            {"alerta": not off},
            "Alerta " + ("apagada" if off else "activada")
        )

    if "compuerta" in t or "puerta" in t:
        return (
            {"compuerta": 0 if off else 90},
            "Compuerta " + ("cerrándose" if off else "abriéndose")
        )

    if "motor" in t:
        return (
            {"motores": 0 if off else 80},
            "Motores " + ("apagados" if off else "al 80 %")
        )

    return None, "Comando no reconocido"


# ==========================================
# INTERPRETAR GESTOS
# ==========================================

def desde_gesto(evento, tele):

    gesto = evento.get("gesto")

    if gesto == "escudos":
        return {"escudos": True}, "Escudos activados (gesto)"

    if gesto == "despegue":
        return {"despegue": True}, "Verificando despegue (gesto)"

    if gesto == "compuerta":

        angulo = (
            0 if tele.get("compuerta", 0) > 0 else 90
        )

        return (
            {"compuerta": angulo},
            "Compuerta " + ("cerrándose" if angulo == 0 else "abriéndose")
        )

    if gesto == "motores":

        valor = int(evento.get("valor") or 0)
        valor = max(0, min(100, valor))

        return (
            {"motores": valor},
            f"Motores al {valor} %"
        )

    if gesto == "alerta":
        return {"alerta": True}, "Alerta activada (gesto)"

    return None, "Gesto desconocido"


# ==========================================
# ESTADO Y BITACORA
# ==========================================

def agregar_log(S, texto):

    S["log"] = [
        time.strftime("%H:%M:%S") + " · " + str(texto)
    ] + S["log"][:7]


# ==========================================
# PUBLICAR COMANDOS
# ==========================================

def publicar_comando(S, client, cmd):

    if not cmd:
        return False

    if not client.is_connected():

        S["pendientes"].append(cmd.copy())

        return False

    resultado = client.publish(
        TOP_COMANDOS,
        json.dumps(cmd),
        qos=1
    )

    if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
        return True

    S["pendientes"].append(cmd.copy())

    return False


def registrar(S, client, cmd, respuesta):

    if cmd:

        enviado = publicar_comando(S, client, cmd)

        if enviado:
            respuesta += " · Orden enviada a MQTT"

        else:
            respuesta += " · Orden pendiente de conexión MQTT"

    S["resp"] = respuesta

    agregar_log(S, respuesta)


# ==========================================
# PROCESAR MENSAJES EN STREAMLIT
# ==========================================

def procesar_eventos(S, client):

    while True:

        try:
            tipo, contenido = S["cola"].get_nowait()

        except queue.Empty:
            break

        # CONEXION
        if tipo == "conexion":

            S["conectado"] = contenido

            if contenido:

                S["resp"] = "Conexión MQTT establecida"

                # Enviar comandos pendientes
                pendientes = S["pendientes"].copy()
                S["pendientes"].clear()

                for cmd in pendientes:

                    resultado = client.publish(
                        TOP_COMANDOS,
                        json.dumps(cmd),
                        qos=1
                    )

                    if resultado.rc != mqtt.MQTT_ERR_SUCCESS:
                        S["pendientes"].append(cmd)

            else:
                S["resp"] = "Conexión MQTT interrumpida"

        # MENSAJES MQTT
        elif tipo == "mensaje":

            topic, datos = contenido

            # TELEMETRIA
            if topic == TOP_TELEMETRIA:

                if isinstance(datos, dict):

                    S["tele"].update(datos)

                    S["ultima_telemetria"] = time.time()

                continue

            # ENTRADA DE GESTOS Y AUDIO
            if topic == TOP_ENTRADA:

                if datos.get("tipo") == "voz":

                    texto = str(datos.get("texto", ""))

                    S["oido"] = texto

                    cmd, respuesta = interpretar(texto)

                else:

                    gesto = datos.get("gesto", "desconocido")

                    S["oido"] = "Gesto: " + str(gesto)

                    cmd, respuesta = desde_gesto(
                        datos,
                        S["tele"]
                    )

                registrar(
                    S,
                    client,
                    cmd,
                    respuesta
                )


# ==========================================
# UNICO NUCLEO MQTT
# ==========================================

@st.cache_resource
def nucleo():

    S = {

        "tele": {},

        "log": [],

        "oido": "—",

        "resp": "Esperando órdenes",

        "conectado": False,

        "cola": queue.Queue(),

        "pendientes": [],

        "ultima_telemetria": None
    }

    def on_connect(
        client,
        userdata,
        flags,
        reason_code,
        properties
    ):

        codigo = getattr(
            reason_code,
            "value",
            reason_code
        )

        conectado = int(codigo) == 0

        S["cola"].put(("conexion", conectado))

        if conectado:

            client.subscribe([
                (TOP_TELEMETRIA, 1),
                (TOP_ENTRADA, 1)
            ])

    def on_disconnect(
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):

        S["cola"].put(("conexion", False))

    def on_message(client, userdata, msg):

        try:

            datos = json.loads(
                msg.payload.decode("utf-8")
            )

            S["cola"].put(
                ("mensaje", (msg.topic, datos))
            )

        except (ValueError, UnicodeDecodeError):
            return

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="NaveStreamlit_" + uuid.uuid4().hex[:10],
        protocol=mqtt.MQTTv311
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.reconnect_delay_set(
        min_delay=1,
        max_delay=30
    )

    client.connect_async(
        BROKER,
        PORT,
        60
    )

    client.loop_start()

    return S, client


# ==========================================
# COMANDOS DESDE AUDIO
# ==========================================

def ejecutar(texto):

    S, client = nucleo()

    S["oido"] = texto

    cmd, respuesta = interpretar(texto)

    registrar(
        S,
        client,
        cmd,
        respuesta
    )


# ==========================================
# COMANDOS MANUALES
# ==========================================

def enviar(**cmd):

    S, client = nucleo()

    registrar(
        S,
        client,
        cmd,
        "Orden manual: " + json.dumps(cmd)
    )


# ==========================================
# VISUALIZACION DE LA NAVE
# ==========================================

def visual():

    archivo = WEB / "visual.html"

    if not archivo.exists():

        st.error(f"No se encuentra el archivo: {archivo}")

        return

    html = archivo.read_text(encoding="utf-8")

    html = html.replace("__PREFIJO__", P)

    components.html(
        html,
        height=440,
        scrolling=False
    )


# ==========================================
# CAPTURA DE GESTOS Y AUDIO
# ==========================================

def captura(modo, h=480):

    archivo = WEB / "captura.html"

    if not archivo.exists():

        st.error(f"No se encuentra el archivo: {archivo}")

        return

    html = archivo.read_text(encoding="utf-8")

    html = html.replace("__PREFIJO__", P)
    html = html.replace("__MODO__", modo)

    components.html(
        html,
        height=h,
        scrolling=False
    )


# ==========================================
# ESTILOS
# ==========================================

def estilos():

    st.markdown("""
    <style>

    @import url(
      'https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap'
    );

    .stApp {
        background: linear-gradient(160deg,#05070f,#1a0b2e);
        color: #d7f8ff;
    }

    h1,h2,h3,h4,
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif !important;
        color: #00f5ff !important;
        text-shadow: 0 0 12px #00f5ff88;
    }

    [data-testid="stMetric"] {
        border: 1px solid #00f5ff66;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 0 14px #00f5ff33;
    }

    .resp {
        border-left: 4px solid #ff2bd6;
        padding: 8px 14px;
        background: #ff2bd610;
        border-radius: 6px;
    }

    </style>
    """, unsafe_allow_html=True)


# ==========================================
# ESTADO EN TIEMPO REAL
# ==========================================

@st.fragment(run_every=1)
def estado():

    S, client = nucleo()

    procesar_eventos(S, client)

    t = S["tele"]

    st.caption(
        "MQTT: " +
        ("CONECTADO" if S["conectado"] else "DESCONECTADO")
    )

    if not t:

        st.warning(
            "Sin telemetría. Comprueba que Wokwi esté ejecutándose."
        )

        st.caption("Esperando datos de la nave espacial...")

        return

    a, b = st.columns(2)

    a.metric(
        "Misión",
        t.get("mision", "—")
    )

    b.metric(
        "Reactor",
        f"{float(t.get('temp', 0)):.1f} °C"
    )

    a, b = st.columns(2)

    a.metric(
        "Escudos",
        "ON" if t.get("escudos") else "OFF"
    )

    b.metric(
        "Compuerta",
        "ABIERTA" if t.get("compuerta", 0) > 0 else "CERRADA"
    )

    a, b = st.columns(2)

    a.metric(
        "Combustible",
        f"{t.get('combustible', 0)} %"
    )

    b.metric(
        "Alerta",
        "ACTIVA" if t.get("alerta") else "INACTIVA"
    )

    a, b = st.columns(2)

    a.metric(
        "Motores",
        f"{t.get('motores', 0)} %"
    )

    b.metric(
        "Meteoritos",
        "DETECTADOS" if t.get("meteoritos") else "NO"
    )

    st.caption("Entendí: " + S["oido"])

    st.markdown(
        f"<div class='resp'>{S['resp']}</div>",
        unsafe_allow_html=True
    )

    if t.get("motivo"):

        st.warning(t["motivo"])

    st.caption("Bitácora")

    st.code(
        "\n".join(S["log"]) or "—"
    )
