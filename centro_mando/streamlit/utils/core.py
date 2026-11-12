
import json
import time
import queue
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import paho.mqtt.client as mqtt


# =====================================================
# CONFIGURACIÓN
# =====================================================

P = "NaveEspacial2026"

BROKER = "broker.hivemq.com"
PORT = 1883

TOP_COMANDOS = f"{P}/comandos"
TOP_TELEMETRIA = f"{P}/telemetria"
TOP_ENTRADA = f"{P}/entrada"

WEB = Path(__file__).resolve().parents[2] / "web"


# =====================================================
# ESTADO Y UTILIDADES
# =====================================================

def normalizar_telemetria(datos):
    d = dict(datos)

    # Compatibilidad con los nombres del ESP32
    if "combustible" not in d and "comb" in d:
        d["combustible"] = d["comb"]

    if "distancia" not in d and "dist" in d:
        d["distancia"] = d["dist"]

    if "emergencia" not in d and "emerg" in d:
        d["emergencia"] = d["emerg"]

    return d


def agregar_log(S, texto):
    hora = time.strftime("%H:%M:%S")
    S["log"] = [f"{hora} · {texto}"] + S["log"][:7]


# =====================================================
# INTERPRETACIÓN DE VOZ
# Se conserva la lógica original
# =====================================================

def interpretar(t):
    t = t.lower().strip()

    off = any(
        w in t
        for w in ("desactiv", "apag", "cerr")
    )

    if "abort" in t:
        return {"despegue": False}, "Misión abortada"

    if "despeg" in t:
        return {"despegue": True}, "Verificando despegue..."

    if "escudo" in t:
        return (
            {"escudos": not off},
            "Escudos " + (
                "desactivados" if off else "activados, capitán"
            )
        )

    if "alerta" in t:
        return (
            {"alerta": not off},
            "Alerta " + (
                "apagada" if off else "roja activada"
            )
        )

    if "compuerta" in t or "puerta" in t:
        return (
            {"compuerta": 0 if off else 90},
            "Compuerta " + (
                "cerrándose" if off else "abriéndose"
            )
        )

    if "motor" in t:
        return (
            {"motores": 0 if off else 80},
            "Motores " + (
                "apagados" if off else "al 80 %"
            )
        )

    return None, "Comando no reconocido"


# =====================================================
# INTERPRETACIÓN DE GESTOS
# Se conserva la lógica original
# =====================================================

def desde_gesto(e, tele):
    g = e.get("gesto")

    if g == "escudos":
        return {
            "escudos": True
        }, "Escudos activados (gesto 👍)"

    if g == "despegue":
        return {
            "despegue": True
        }, "Verificando despegue (gesto 🤘)"

    if g == "compuerta":
        a = 0 if float(tele.get("compuerta", 0) or 0) > 0 else 90

        return (
            {"compuerta": a},
            "Compuerta " + (
                "cerrándose" if a == 0 else "abriéndose"
            )
        )

    if g == "motores":
        v = int(e.get("valor") or 0)
        v = max(0, min(100, v))

        return {
            "motores": v
        }, f"Motores al {v} %"

    return None, "Gesto desconocido"


# =====================================================
# PUBLICAR COMANDOS DESDE STREAMLIT
# =====================================================

def registrar(S, client, cmd, resp):

    if cmd:

        if not client.is_connected():
            S["resp"] = "MQTT desconectado. No se pudo enviar la orden."
            agregar_log(S, S["resp"])
            return

        try:
            resultado = client.publish(
                TOP_COMANDOS,
                json.dumps(cmd),
                qos=1
            )

            if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
                resp += " · Orden enviada; esperando confirmación del ESP32"
            else:
                resp += " · Error al publicar la orden MQTT"

        except Exception as e:
            resp += f" · Error MQTT: {e}"

    S["resp"] = resp
    agregar_log(S, resp)


def enviar(**cmd):
    S, client = nucleo()

    registrar(
        S,
        client,
        cmd,
        "Orden manual: " + json.dumps(cmd)
    )


def ejecutar(texto):
    S, client = nucleo()

    S["oido"] = texto

    cmd, resp = interpretar(texto)

    registrar(S, client, cmd, resp)


# =====================================================
# PROCESAMIENTO DE MENSAJES
# Esta función se ejecuta desde Streamlit,
# NO desde el hilo MQTT.
# =====================================================

def procesar_eventos(S, client):

    while True:
        try:
            tipo, contenido = S["cola"].get_nowait()
        except queue.Empty:
            break

        # ---------------------------------------------
        # CONEXIÓN MQTT
        # ---------------------------------------------

        if tipo == "conexion":

            S["conectado"] = contenido

            if contenido:
                S["resp"] = "Conexión MQTT establecida"

                agregar_log(
                    S,
                    "Conexión con HiveMQ establecida"
                )

                # Reintentar suscripciones
                client.subscribe([
                    (TOP_TELEMETRIA, 1),
                    (TOP_ENTRADA, 1)
                ])

            else:
                S["resp"] = "Conexión MQTT interrumpida"

                agregar_log(
                    S,
                    "Conexión MQTT interrumpida"
                )

        # ---------------------------------------------
        # MENSAJES MQTT
        # ---------------------------------------------

        elif tipo == "mensaje":

            topic, datos = contenido

            # TELEMETRÍA DEL ESP32
            if topic == TOP_TELEMETRIA:

                datos = normalizar_telemetria(datos)

                S["tele"].update(datos)

                S["ultima_telemetria"] = time.time()

            # ENTRADAS DE VOZ Y GESTOS
            elif topic == TOP_ENTRADA:

                if datos.get("tipo") == "voz":

                    texto = str(datos.get("texto", ""))

                    S["oido"] = texto

                    cmd, resp = interpretar(texto)

                elif datos.get("tipo") == "gesto":

                    gesto = datos.get("gesto", "desconocido")

                    S["oido"] = "gesto: " + str(gesto)

                    cmd, resp = desde_gesto(
                        datos,
                        S["tele"]
                    )

                else:
                    cmd = None
                    resp = "Entrada MQTT desconocida"

                registrar(
                    S,
                    client,
                    cmd,
                    resp
                )


# =====================================================
# NÚCLEO MQTT COMPARTIDO
# =====================================================

@st.cache_resource
def nucleo():

    S = {
        "tele": {},
        "log": [],
        "oido": "—",
        "resp": "Esperando órdenes",
        "conectado": False,
        "cola": queue.Queue(),
        "ultima_telemetria": None
    }

    # Paho MQTT 1.6.1: callbacks API versión 1
    def on_connect(client, userdata, flags, rc):

        if rc == 0:

            S["cola"].put(
                ("conexion", True)
            )

            client.subscribe([
                (TOP_TELEMETRIA, 1),
                (TOP_ENTRADA, 1)
            ])

        else:

            S["cola"].put(
                ("conexion", False)
            )

    def on_disconnect(client, userdata, rc):

        S["cola"].put(
            ("conexion", False)
        )

    def on_message(client, userdata, msg):

        try:

            datos = json.loads(
                msg.payload.decode("utf-8")
            )

            # El hilo MQTT solamente coloca el mensaje
            # en la cola. No modifica la interfaz.
            S["cola"].put(
                ("mensaje", (msg.topic, datos))
            )

        except (
            ValueError,
            UnicodeDecodeError
        ):
            return

    client = mqtt.Client(
        client_id="NaveStreamlit_" + uuid.uuid4().hex[:10],
        clean_session=True
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


# =====================================================
# VISUALIZACIÓN HTML
# =====================================================

def visual():

    archivo = WEB / "visual.html"

    if not archivo.exists():
        st.error(f"No se encuentra el archivo: {archivo}")
        return

    html = archivo.read_text(encoding="utf-8")

    html = html.replace(
        "__PREFIJO__",
        P
    )

    components.html(
        html,
        height=440,
        scrolling=False
    )


# =====================================================
# CAPTURA HTML
# Se conserva el modo original
# =====================================================

def captura(modo, h=480):

    archivo = WEB / "captura.html"

    if not archivo.exists():
        st.error(f"No se encuentra el archivo: {archivo}")
        return

    html = archivo.read_text(encoding="utf-8")

    html = html.replace(
        "__PREFIJO__",
        P
    )

    html = html.replace(
        "__MODO__",
        modo
    )

    components.html(
        html,
        height=h,
        scrolling=False
    )


# =====================================================
# ESTILOS
# =====================================================

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
        font-family: 'Orbitron',sans-serif !important;
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


# =====================================================
# PANEL DE ESTADO
# Lee la telemetría real del ESP32
# =====================================================

@st.fragment(run_every=1)
def estado():

    S, client = nucleo()

    # Procesar mensajes pendientes
    procesar_eventos(S, client)

    t = S["tele"]

    st.markdown("### ESTADO DE LA NAVE")

    if S["conectado"]:
        st.success("MQTT conectado con HiveMQ")
    else:
        st.warning("Conectando con HiveMQ...")

    if not t:

        st.warning(
            "Esperando telemetría del ESP32 de Wokwi..."
        )

    else:

        temp = float(t.get("temp", 0) or 0)
        comb = float(t.get("combustible", 0) or 0)
        dist = float(t.get("distancia", 0) or 0)
        motores = float(t.get("motores", 0) or 0)
        compuerta = float(t.get("compuerta", 0) or 0)

        a, b = st.columns(2)

        a.metric(
            "Misión",
            str(t.get("mision", "—"))
        )

        b.metric(
            "Reactor",
            f"{temp:.1f} °C"
        )

        a, b = st.columns(2)

        a.metric(
            "Escudos",
            "ACTIVADOS" if t.get("escudos") else "DESACTIVADOS"
        )

        b.metric(
            "Compuerta",
            "ABIERTA" if compuerta > 0 else "CERRADA"
        )

        a, b = st.columns(2)

        a.metric(
            "Combustible",
            f"{comb:.0f} %"
        )

        b.metric(
            "Motores",
            f"{motores:.0f} %"
        )

        a, b = st.columns(2)

        a.metric(
            "Radar",
            f"{dist:.1f} cm"
        )

        b.metric(
            "Alerta",
            "ACTIVA" if t.get("alerta") else "NORMAL"
        )

        if t.get("meteoritos"):
            st.warning("¡Meteoritos detectados!")

        if t.get("emergencia"):
            st.error("¡EMERGENCIA ACTIVA!")

        if t.get("motivo"):
            st.warning(str(t["motivo"]))

        if S["ultima_telemetria"] is not None:

            edad = time.time() - S["ultima_telemetria"]

            st.caption(
                f"Última telemetría recibida hace {edad:.1f} segundos"
            )

    st.caption(
        "Entrada reconocida: " + str(S["oido"])
    )

    st.markdown(
        f"<div class='resp'>{S['resp']}</div>",
        unsafe_allow_html=True
    )

    st.caption("BITÁCORA")

    st.code(
        "\n".join(S["log"]) or "Esperando eventos..."
    )
