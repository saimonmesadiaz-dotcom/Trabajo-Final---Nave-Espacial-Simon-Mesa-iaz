
import json
import time
import uuid
import queue
import unicodedata
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import paho.mqtt.client as mqtt


# =========================================================
# CONFIGURACIÓN MQTT
# =========================================================

P = "NaveEspacial2026"

BROKER = "broker.hivemq.com"
PORT = 1883

TOP_ENTRADA = f"{P}/entrada"
TOP_COMANDOS = f"{P}/comandos"
TOP_TELEMETRIA = f"{P}/telemetria"

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"


# =========================================================
# NORMALIZACIÓN DE TEXTO
# =========================================================

def normalizar(texto):
    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto


# =========================================================
# INTERPRETACIÓN DE VOZ
# =========================================================

def interpretar(texto):

    t = normalizar(texto)

    off = any(
        palabra in t
        for palabra in ("desactiv", "apag", "cerr")
    )

    if "abort" in t:
        return {
            "despegue": False,
            "emergencia": True
        }, "Misión abortada: emergencia activada"

    if "despeg" in t:
        return {
            "despegue": True
        }, "Verificando condiciones de despegue..."

    if "escudo" in t:
        return {
            "escudos": not off
        }, (
            "Escudos desactivados"
            if off else
            "Escudos activados, capitán"
        )

    if "alerta" in t:
        return {
            "alerta": not off
        }, (
            "Alerta manual apagada"
            if off else
            "Alerta manual activada"
        )

    if "compuerta" in t or "puerta" in t:

        angulo = 0 if off else 90

        return {
            "compuerta": angulo
        }, (
            "Compuerta cerrándose"
            if off else
            "Compuerta abriéndose"
        )

    if "motor" in t:

        velocidad = 0 if off else 80

        return {
            "motores": velocidad
        }, (
            "Motores apagados"
            if off else
            "Motores al 80 %"
        )

    return None, "Comando de voz no reconocido"


# =========================================================
# INTERPRETACIÓN DE GESTOS
# =========================================================

def desde_gesto(evento, tele):

    gesto = evento.get("gesto")

    if gesto == "escudos":

        return {
            "escudos": True
        }, "Escudos activados mediante gesto"

    if gesto == "despegue":

        return {
            "despegue": True
        }, "Verificando despegue mediante gesto"

    if gesto == "compuerta":

        actual = float(tele.get("compuerta", 0) or 0)

        angulo = 0 if actual > 0 else 90

        return {
            "compuerta": angulo
        }, (
            "Compuerta cerrándose"
            if angulo == 0 else
            "Compuerta abriéndose"
        )

    if gesto == "motores":

        velocidad = int(evento.get("valor") or 0)
        velocidad = max(0, min(100, velocidad))

        return {
            "motores": velocidad
        }, f"Motores al {velocidad} %"

    return None, "Gesto no reconocido"


# =========================================================
# NORMALIZACIÓN DE TELEMETRÍA
# =========================================================

def normalizar_telemetria(datos):

    d = dict(datos)

    # Compatibilidad con nombres del ESP32
    if "combustible" not in d and "comb" in d:
        d["combustible"] = d["comb"]

    if "distancia" not in d and "dist" in d:
        d["distancia"] = d["dist"]

    if "emergencia" not in d and "emerg" in d:
        d["emergencia"] = d["emerg"]

    if "vuelo" in d and "mision" not in d:
        d["mision"] = "EN VUELO" if d["vuelo"] else "PLATAFORMA"

    if "meteoritos" not in d:
        try:
            d["meteoritos"] = (
                float(d.get("temp", 0)) > 30
                and not bool(d.get("escudos", False))
            )
        except (TypeError, ValueError):
            d["meteoritos"] = False

    if "alerta" not in d:
        d["alerta"] = (
            bool(d.get("alertaMan", False))
            or bool(d.get("meteoritos", False))
            or bool(d.get("emergencia", False))
        )

    return d


# =========================================================
# BITÁCORA
# =========================================================

def agregar_log(S, texto):

    hora = time.strftime("%H:%M:%S")

    S["log"] = [
        f"{hora} · {texto}"
    ] + S["log"][:7]


# =========================================================
# PUBLICACIÓN DE COMANDOS
# =========================================================

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
            respuesta += " · Publicada en MQTT"
        else:
            respuesta += " · Pendiente de conexión MQTT"

    S["resp"] = respuesta

    agregar_log(S, respuesta)


# =========================================================
# PROCESAMIENTO DE EVENTOS MQTT
# =========================================================

def procesar_eventos(S, client):

    while True:

        try:
            tipo, contenido = S["cola"].get_nowait()

        except queue.Empty:
            break

        # ---------------------------------------------
        # ESTADO DE CONEXIÓN
        # ---------------------------------------------

        if tipo == "conexion":

            conectado = bool(contenido)

            S["conectado"] = conectado

            if conectado:

                S["resp"] = "Conexión MQTT establecida"

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

        # ---------------------------------------------
        # MENSAJES RECIBIDOS
        # ---------------------------------------------

        elif tipo == "mensaje":

            topic, datos = contenido

            # TELEMETRÍA DEL ESP32
            if topic == TOP_TELEMETRIA:

                datos = normalizar_telemetria(datos)

                S["tele"].update(datos)

                S["ultima_telemetria"] = time.time()

            # ENTRADA DE VOZ Y GESTOS
            elif topic == TOP_ENTRADA:

                if datos.get("tipo") == "voz":

                    texto = str(datos.get("texto", ""))

                    S["oido"] = texto

                    cmd, respuesta = interpretar(texto)

                elif datos.get("tipo") == "gesto":

                    gesto = datos.get("gesto", "desconocido")

                    S["oido"] = "Gesto: " + str(gesto)

                    cmd, respuesta = desde_gesto(
                        datos,
                        S["tele"]
                    )

                else:

                    cmd = None
                    respuesta = "Entrada MQTT desconocida"

                registrar(
                    S,
                    client,
                    cmd,
                    respuesta
                )


# =========================================================
# CONEXIÓN MQTT COMPARTIDA
# =========================================================

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

        S["cola"].put(
            ("conexion", conectado)
        )

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

        S["cola"].put(
            ("conexion", False)
        )

    def on_message(client, userdata, msg):

        try:

            datos = json.loads(
                msg.payload.decode("utf-8")
            )

            S["cola"].put(
                ("mensaje", (msg.topic, datos))
            )

        except (
            ValueError,
            UnicodeDecodeError
        ):
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


# =========================================================
# FUNCIONES PARA ÓRDENES MANUALES
# =========================================================

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


def enviar(**cmd):

    S, client = nucleo()

    registrar(
        S,
        client,
        cmd,
        "Orden manual: " + json.dumps(cmd)
    )


# =========================================================
# VISUALIZACIÓN HTML
# =========================================================

def visual():

    archivo = WEB / "visual.html"

    if not archivo.exists():

        st.error(f"No se encuentra {archivo}")
        return

    html = archivo.read_text(
        encoding="utf-8"
    )

    html = html.replace(
        "__PREFIJO__",
        P
    )

    components.html(
        html,
        height=440,
        scrolling=False
    )


# =========================================================
# CAPTURA HTML
# =========================================================

def captura(modo, h=480):

    if modo not in ("gest", "voz"):

        st.error("Modo de captura no válido")
        return

    archivo = WEB / "captura.html"

    if not archivo.exists():

        st.error(f"No se encuentra {archivo}")
        return

    html = archivo.read_text(
        encoding="utf-8"
    )

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


# =========================================================
# ESTILOS
# =========================================================

def estilos():

    st.markdown(
        """
        <style>

        @import url(
          'https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap'
        );

        .stApp {
            background: linear-gradient(
                160deg,
                #05070f,
                #1a0b2e
            );
            color: #d7f8ff;
        }

        h1, h2, h3, h4,
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
        """,
        unsafe_allow_html=True
    )


# =========================================================
# PANEL DE ESTADO
# =========================================================

@st.fragment(run_every=1)
def estado():

    S, client = nucleo()

    procesar_eventos(S, client)

    t = S["tele"]

    st.subheader("CENTRO DE CONTROL")

    if S["conectado"]:

        st.success("MQTT conectado")

    else:

        st.warning("Conectando con HiveMQ...")

    if not t:

        st.warning(
            "Sin telemetría. Comprueba que Wokwi esté "
            "ejecutándose y que el prefijo MQTT coincida."
        )

    else:

        # Valores numéricos seguros
        try:
            temperatura = float(t.get("temp", 0) or 0)
        except (TypeError, ValueError):
            temperatura = 0.0

        try:
            combustible = float(t.get("combustible", 0) or 0)
        except (TypeError, ValueError):
            combustible = 0.0

        try:
            distancia = float(t.get("distancia", 0) or 0)
        except (TypeError, ValueError):
            distancia = 0.0

        try:
            motores = float(t.get("motores", 0) or 0)
        except (TypeError, ValueError):
            motores = 0.0

        compuerta = float(t.get("compuerta", 0) or 0)

        mision = t.get("mision", "—")

        a, b = st.columns(2)

        a.metric("Misión", str(mision))
        b.metric("Reactor", f"{temperatura:.1f} °C")

        a, b = st.columns(2)

        a.metric(
            "Escudos",
            "ON" if t.get("escudos") else "OFF"
        )

        b.metric(
            "Compuerta",
            "ABIERTA" if compuerta > 0 else "CERRADA"
        )

        a, b = st.columns(2)

        a.metric(
            "Combustible",
            f"{combustible:.0f} %"
        )

        b.metric(
            "Motores",
            f"{motores:.0f} %"
        )

        a, b = st.columns(2)

        a.metric(
            "Radar",
            f"{distancia:.1f} cm"
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

        if S["ultima_telemetria"]:

            edad = time.time() - S["ultima_telemetria"]

            st.caption(
                f"Última telemetría hace {edad:.1f} segundos"
            )

    st.caption("Entrada reconocida: " + str(S["oido"]))

    st.markdown(
        f"<div class='resp'>{S['resp']}</div>",
        unsafe_allow_html=True
    )

    st.caption("BITÁCORA DE LA MISIÓN")

    st.code(
        "\n".join(S["log"]) or "Esperando eventos..."
    )
