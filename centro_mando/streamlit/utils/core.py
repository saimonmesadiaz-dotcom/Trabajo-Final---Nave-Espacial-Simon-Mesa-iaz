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
# CATÁLOGO DE COMANDOS (se muestra al usuario como guía)
# =====================================================

COMANDOS_VOZ = [
    ("🛡️ Escudos", ["activar escudos", "desactivar escudos"]),
    ("🚪 Compuerta", ["abrir compuerta", "cerrar compuerta"]),
    ("🚨 Alerta", ["alerta roja", "alerta extrema", "alerta normal"]),
    ("🔥 Motores", ["encender motores", "apagar motores"]),
    ("🚀 Misión", ["iniciar despegue", "abortar misión"]),
]

GESTOS = [
    ("👍", "Pulgar arriba", "Activar escudos"),
    ("🖐️", "Mano abierta", "Abrir / cerrar compuerta"),
    ("🤘", "Índice y meñique", "Iniciar despegue"),
    ("✊", "Puño cerrado", "Motores al 0 %"),
    ("☝️", "1 a 4 dedos", "Motores al 25 – 100 %"),
]

REQUISITOS_DESPEGUE = (
    "Para despegar: escudos activos (\"activar escudos\"), "
    "compuerta cerrada (\"cerrar compuerta\") y combustible de al menos 30 %."
)


def _limpiar(t):
    t = t.lower().strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        t = t.replace(a, b)
    return t


def nivel_alerta(t):
    """NORMAL / ROJA / EXTREMA a partir de la telemetría."""
    if t.get("nivel") in ("NORMAL", "ROJA", "EXTREMA"):
        return t["nivel"]
    if t.get("emergencia"):
        return "EXTREMA"
    if t.get("alerta") or t.get("meteoritos"):
        return "ROJA"
    return "NORMAL"


def interpretar(t):
    t = _limpiar(t)

    off = any(w in t for w in (
        "desactiv", "apag", "cerr", "cierr", "baja", "quita", "normal"
    ))

    if "abort" in t or "cancel" in t:
        return {"despegue": False}, "Misión abortada"

    if "despeg" in t or "lanz" in t:
        return {"despegue": True}, "Verificando despegue..."

    if "escudo" in t:
        return (
            {"escudos": not off},
            "Escudos " + ("desactivados" if off else "activados, capitán")
        )

    if "alerta" in t or "emergencia" in t:
        if "extrem" in t or "emergencia" in t:
            return {"extrema": not off}, "Alerta roja EXTREMA " + (
                "desactivada" if off else "activada")
        if off:
            return {"alerta": False, "extrema": False}, "Alerta normal"
        return {"alerta": True}, "Alerta roja activada"

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

    return None, "Comando no reconocido: \"" + t + "\""


# =====================================================
# INTERPRETACIÓN DE GESTOS
# =====================================================

def desde_gesto(e, tele):
    g = e.get("gesto")

    if g == "escudos":
        return {"escudos": True}, "Escudos activados (gesto 👍)"

    if g == "despegue":
        return {"despegue": True}, "Verificando despegue (gesto 🤘)"

    if g == "compuerta":
        a = 0 if float(tele.get("compuerta", 0) or 0) > 0 else 90
        return (
            {"compuerta": a},
            "Compuerta " + ("cerrándose" if a == 0 else "abriéndose")
        )

    if g == "motores":
        v = max(0, min(100, int(e.get("valor") or 0)))
        return {"motores": v}, f"Motores al {v} %"

    return None, "Gesto desconocido"


# =====================================================
# AVISOS (aparecen en el encabezado fijo)
# =====================================================

def avisar(S, nivel, texto, ayuda=""):
    """nivel: ok | info | warn | error"""
    S["aviso"] = {
        "nivel": nivel, "texto": texto, "ayuda": ayuda, "t": time.time()
    }


def validar(cmd, tele):
    """
    Revisa la orden contra la última telemetría ANTES de enviarla.
    Devuelve (permitida, texto_de_error, ayuda).
    Si aún no hay telemetría no bloquea: el ESP32 decide.
    """
    if not tele or not cmd:
        return True, "", ""

    comb = float(tele.get("combustible", 0) or 0)
    en_vuelo = tele.get("mision") == "EN VUELO"

    if cmd.get("despegue") is True:
        if en_vuelo:
            return False, "La nave ya está en vuelo", \
                "Di \"abortar misión\" para volver a la plataforma."
        if not tele.get("escudos"):
            return False, "Escudos desactivados", \
                "Di \"activar escudos\" y luego \"iniciar despegue\"."
        if float(tele.get("compuerta", 0) or 0) > 0:
            return False, "Compuerta abierta", \
                "Di \"cerrar compuerta\" y luego \"iniciar despegue\"."
        if comb < 30:
            return False, f"Combustible bajo ({comb:.0f} %)", \
                "Sube el potenciómetro de Wokwi por encima de 30 % " \
                "y repite \"iniciar despegue\"."

    if "compuerta" in cmd and en_vuelo:
        return False, "No se puede mover la compuerta en vuelo", \
            "Di \"abortar misión\" primero."

    if cmd.get("alerta") is False and tele.get("meteoritos"):
        return False, "Hay meteoritos: la alerta no puede apagarse", \
            "Di \"activar escudos\" y la alerta se normalizará sola."

    return True, "", ""


def coincide(cmd, tele):
    """¿La telemetría ya refleja lo que se pidió?"""
    if "escudos" in cmd and bool(tele.get("escudos")) != bool(cmd["escudos"]):
        return False
    if "compuerta" in cmd and (
        (float(tele.get("compuerta", 0) or 0) > 0) != (cmd["compuerta"] > 0)
    ):
        return False
    if "motores" in cmd and abs(
        float(tele.get("motores", 0) or 0) - cmd["motores"]
    ) > 1:
        return False
    if "alerta" in cmd and cmd["alerta"] is False:
        return nivel_alerta(tele) == "NORMAL" or bool(tele.get("meteoritos"))
    if "alerta" in cmd and cmd["alerta"] is True:
        return nivel_alerta(tele) != "NORMAL"
    if "extrema" in cmd and (
        (nivel_alerta(tele) == "EXTREMA") != bool(cmd["extrema"])
    ):
        return False
    if cmd.get("despegue") is True:
        return tele.get("mision") == "EN VUELO"
    if cmd.get("despegue") is False:
        return tele.get("mision") == "ABORTADO"
    return True


# =====================================================
# PUBLICAR COMANDOS DESDE STREAMLIT
# =====================================================

def registrar(S, client, cmd, resp):

    if cmd:

        permitida, error, ayuda = validar(cmd, S["tele"])

        if not permitida:
            S["resp"] = f"⛔ {error}. {ayuda}"
            agregar_log(S, f"Orden rechazada: {error}")
            avisar(S, "error", error, ayuda)
            return

        if not client.is_connected():
            S["resp"] = "MQTT desconectado. No se pudo enviar la orden."
            agregar_log(S, S["resp"])
            avisar(S, "error", "MQTT desconectado",
                   "Revisa tu conexión a internet.")
            return

        try:
            resultado = client.publish(
                TOP_COMANDOS, json.dumps(cmd), qos=1
            )

            if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
                S["pendiente"] = {
                    "cmd": cmd, "texto": resp, "t": time.time()
                }
                avisar(S, "info", resp, "Esperando confirmación del ESP32...")
                resp += " · enviada, esperando confirmación"
            else:
                resp += " · Error al publicar la orden MQTT"
                avisar(S, "error", "Error al publicar la orden MQTT")

        except Exception as e:
            resp += f" · Error MQTT: {e}"
            avisar(S, "error", "Error MQTT", str(e))

    else:
        avisar(S, "warn", resp,
               "Revisa la lista de comandos de ejemplo.")

    S["resp"] = resp
    agregar_log(S, resp)


def revisar_confirmacion(S):
    """Se llama tras cada telemetría y cada segundo."""
    p = S.get("pendiente")
    if not p:
        return

    tele = S["tele"]
    edad = time.time() - p["t"]

    if tele and coincide(p["cmd"], tele):
        if S.get("ultima_telemetria") and S["ultima_telemetria"] >= p["t"]:
            S["pendiente"] = None
            avisar(S, "ok", "✔ Confirmado por el ESP32: " + p["texto"])
            agregar_log(S, "Confirmado: " + p["texto"])
            return

    if edad > 1.5 and tele and S.get("ultima_telemetria", 0) >= p["t"]:
        # Llegó telemetría posterior y no refleja el cambio: el ESP32 lo rechazó
        S["pendiente"] = None
        motivo = tele.get("motivo") or "El ESP32 no aplicó la orden"
        avisar(S, "error", motivo, REQUISITOS_DESPEGUE
               if p["cmd"].get("despegue") else "")
        agregar_log(S, "Rechazada por ESP32: " + motivo)
        return

    if edad > 6:
        S["pendiente"] = None
        avisar(S, "warn", "Sin respuesta del ESP32",
               "¿Está corriendo la simulación en Wokwi?")
        agregar_log(S, "Sin confirmación del ESP32")


def enviar(**cmd):
    S, client = nucleo()
    registrar(S, client, cmd, "Orden manual: " + json.dumps(cmd))


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

                revisar_confirmacion(S)

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

    revisar_confirmacion(S)


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
        "ultima_telemetria": None,
        "pendiente": None,
        "aviso": None
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
# AYUDANTES HTML
# =====================================================

def html(texto):
    """Compacta el HTML (sin sangrías ni líneas vacías) para que
    Markdown no lo confunda con un bloque de código."""
    st.markdown(
        "".join(l.strip() for l in texto.splitlines()),
        unsafe_allow_html=True
    )


def chip(etiqueta, valor, clase):
    return (
        f"<div class='chip {clase}'>"
        f"<span class='chip-l'>{etiqueta}</span>"
        f"<span class='chip-v'>{valor}</span></div>"
    )


# =====================================================
# VISUALIZACIÓN HTML
# =====================================================

def visual():

    archivo = WEB / "visual.html"

    if not archivo.exists():
        st.error(f"No se encuentra el archivo: {archivo}")
        return

    html_ = archivo.read_text(encoding="utf-8").replace("__PREFIJO__", P)

    components.html(html_, height=500, scrolling=False)


# =====================================================
# CAPTURA HTML (voz / gestos)
# =====================================================

def captura(modo, h=480):

    archivo = WEB / "captura.html"

    if not archivo.exists():
        st.error(f"No se encuentra el archivo: {archivo}")
        return

    # La página usa "gest"; aceptamos "gestos" por comodidad
    modo = "gest" if modo.startswith("gest") else modo

    html_ = (
        archivo.read_text(encoding="utf-8")
        .replace("__PREFIJO__", P)
        .replace("__MODO__", modo)
    )

    components.html(html_, height=h, scrolling=False)


# =====================================================
# ESTILOS DE COMPONENTES PROPIOS
# =====================================================

def estilos():

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap');

.resp{border-left:4px solid #ff2bd6;padding:8px 14px;background:#ff2bd610;border-radius:6px;color:#ffd9f6}

/* ---------- fichas de estado ---------- */
.rejilla{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:8px 0}
.chip{border-radius:14px;padding:11px 14px;border:1px solid rgba(0,234,255,.35);
  background:linear-gradient(145deg,rgba(17,31,61,.95),rgba(13,13,37,.9));
  display:flex;flex-direction:column;gap:3px;transition:all .25s}
.chip:hover{transform:translateY(-2px);box-shadow:0 0 18px rgba(0,234,255,.25)}
.chip-l{font-size:11px;letter-spacing:2px;color:#8fb0cf}
.chip-v{font-family:Orbitron,sans-serif;font-size:17px;font-weight:700}
.c-ok{border-color:rgba(0,255,150,.55)} .c-ok .chip-v{color:#2dffa0;text-shadow:0 0 10px #2dffa066}
.c-off{border-color:rgba(130,150,180,.35)} .c-off .chip-v{color:#8fa4bd}
.c-warn{border-color:rgba(255,212,0,.6)} .c-warn .chip-v{color:#ffd400;text-shadow:0 0 10px #ffd40066}
.c-bad{border-color:rgba(255,59,90,.7);animation:latido 1.1s infinite}
.c-bad .chip-v{color:#ff4d6a;text-shadow:0 0 10px #ff4d6a88}
.c-info .chip-v{color:#00eaff}
@keyframes latido{50%{box-shadow:0 0 20px rgba(255,59,90,.55)}}

.barra{height:8px;border-radius:6px;background:#0a1226;overflow:hidden;margin-top:4px}
.barra>i{display:block;height:100%;border-radius:6px;transition:width .6s}

/* ---------- lista de comandos ---------- */
.cmd-grupo{border:1px solid rgba(155,92,255,.4);border-radius:14px;padding:10px 14px;
  background:rgba(14,22,46,.7);margin-bottom:10px}
.cmd-titulo{font-family:Orbitron,sans-serif;font-size:13px;color:#00eaff;margin-bottom:6px}
.cmd{display:inline-block;margin:3px 6px 3px 0;padding:4px 11px;border-radius:20px;
  border:1px solid rgba(0,234,255,.45);background:rgba(0,234,255,.08);color:#dff8ff;font-size:13px}
.cmd:before{content:"🎙️ ";font-size:11px}
.gesto{display:flex;align-items:center;gap:12px;padding:6px 4px;border-bottom:1px solid rgba(0,234,255,.12)}
.gesto b{font-size:26px;width:38px;text-align:center}
.gesto span{color:#9fb8d3;font-size:13px}

/* ---------- encabezado fijo ---------- */
.enc{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;padding:9px 14px;
  border:1px solid rgba(0,234,255,.4);border-radius:14px;
  background:linear-gradient(100deg,rgba(8,16,40,.96),rgba(26,14,52,.96));
  box-shadow:0 6px 24px rgba(0,0,0,.45)}
.pill{display:inline-flex;align-items:center;gap:7px;padding:4px 11px;border-radius:20px;
  font-size:12px;letter-spacing:.5px;border:1px solid;white-space:nowrap}
.pill i{width:9px;height:9px;border-radius:50%;display:inline-block}
.p-ok{color:#2dffa0;border-color:#2dffa066;background:#2dffa010}.p-ok i{background:#2dffa0;box-shadow:0 0 8px #2dffa0}
.p-bad{color:#ff6a80;border-color:#ff4d6a66;background:#ff4d6a10}.p-bad i{background:#ff4d6a;box-shadow:0 0 8px #ff4d6a}
.p-warn{color:#ffd400;border-color:#ffd40066;background:#ffd40010}.p-warn i{background:#ffd400;box-shadow:0 0 8px #ffd400}
.p-info{color:#00eaff;border-color:#00eaff66;background:#00eaff10}.p-info i{background:#00eaff;box-shadow:0 0 8px #00eaff}
.aviso{flex:1 1 320px;display:flex;gap:10px;align-items:center;padding:6px 12px;border-radius:10px;
  font-size:13px;border:1px solid;min-width:260px}
.aviso b{font-size:20px}
.a-error{background:#ff2b4a1c;border-color:#ff4d6a;color:#ffd3da;animation:latido 1.1s 3}
.a-warn{background:#ffd4001a;border-color:#ffd400;color:#fff0a8}
.a-ok{background:#2dffa016;border-color:#2dffa0;color:#c9ffe6}
.a-info{background:#00eaff14;border-color:#00eaff;color:#c9f8ff}
.aviso small{display:block;opacity:.85;margin-top:1px}
.aviso-vacio{flex:1 1 320px;color:#6f89a6;font-size:13px;padding-left:6px}
</style>
""", unsafe_allow_html=True)


# =====================================================
# ENCABEZADO FIJO: estado de conexión + avisos
# =====================================================

def _pill(clase, texto):
    return f"<span class='pill p-{clase}'><i></i>{texto}</span>"


@st.fragment(run_every=1)
def _encabezado_vivo():

    S, client = nucleo()
    procesar_eventos(S, client)

    t = S["tele"]
    ahora = time.time()

    pills = []

    if S["conectado"]:
        pills.append(_pill("ok", "HiveMQ conectado"))
    else:
        pills.append(_pill("warn", "Conectando con HiveMQ..."))

    ult = S["ultima_telemetria"]

    if ult is None:
        pills.append(_pill("warn", "Wokwi: esperando telemetría"))
    elif ahora - ult < 4:
        pills.append(_pill("ok", f"Wokwi en línea · {ahora - ult:.0f} s"))
    else:
        pills.append(_pill("bad", f"Wokwi sin señal · {ahora - ult:.0f} s"))

    if t:
        nivel = nivel_alerta(t)
        pills.append(_pill(
            {"NORMAL": "ok", "ROJA": "bad", "EXTREMA": "bad"}[nivel],
            {"NORMAL": "Alerta normal",
             "ROJA": "ALERTA ROJA",
             "EXTREMA": "ALERTA ROJA EXTREMA"}[nivel]
        ))
        pills.append(_pill("info", "Misión: " + str(t.get("mision", "—"))))

    a = S.get("aviso")

    if a and ahora - a["t"] < 20:
        icono = {"ok": "✅", "info": "📡", "warn": "⚠️", "error": "🚨"}[a["nivel"]]
        ayuda = f"<small>{a['ayuda']}</small>" if a["ayuda"] else ""
        aviso = (
            f"<div class='aviso a-{a['nivel']}'><b>{icono}</b>"
            f"<div>{a['texto']}{ayuda}</div></div>"
        )
    else:
        aviso = (
            "<div class='aviso-vacio'>Sin avisos · "
            "las confirmaciones y errores aparecerán aquí</div>"
        )

    html("<div class='enc'>" + "".join(pills) + aviso + "</div>")


def encabezado():
    """Barra superior fija con conexión, estado y avisos."""
    with st.container(key="header_fijo"):
        _encabezado_vivo()


# =====================================================
# BARRA LATERAL: explicación de la interfaz
# =====================================================

def guia_lateral():
    with st.sidebar:
        html("""
<div class='destellos'>
<i style='left:12%;top:60px;animation-delay:0s'></i>
<i style='left:80%;top:140px;animation-delay:1.1s'></i>
<i style='left:30%;top:260px;animation-delay:2.3s'></i>
<i style='left:68%;top:340px;animation-delay:.6s'></i>
<i style='left:15%;top:430px;animation-delay:3.1s'></i>
<i style='left:88%;top:500px;animation-delay:1.8s'></i>
<i style='left:45%;top:600px;animation-delay:2.7s'></i>
</div>
<div class='guia'>
<div class='guia-t'>🛰️ BIENVENIDO, CAPITÁN</div>
<p>Esta interfaz te permite controlar una nave simulada en Wokwi (ESP32) usando tu <b>voz</b> o tus <b>gestos</b>.</p>
<div class='guia-t'>CÓMO LEER LA PANTALLA</div>
<ul>
<li><b>Encabezado superior:</b> muestra si hay conexión con HiveMQ y con Wokwi, el nivel de alerta y los avisos. Si una orden no se puede cumplir, ahí te explica por qué.</li>
<li><b>Tablero de la nave:</b> el cohete y la telemetría real: reactor, combustible, radar, escudos y compuerta.</li>
<li><b>Estado de la nave:</b> confirma cada orden y guarda la bitácora.</li>
</ul>
<div class='guia-t'>DÓNDE DAR ÓRDENES</div>
<ul>
<li><b>Puente de Mando:</b> órdenes por voz o por texto.</li>
<li><b>Sala de Máquinas:</b> gestos con la cámara y controles manuales.</li>
</ul>
<div class='guia-t'>PARA DESPEGAR</div>
<ol>
<li>Activa los escudos.</li>
<li>Cierra la compuerta.</li>
<li>Comprueba que el combustible sea de al menos 30 %.</li>
<li>Di «iniciar despegue».</li>
</ol>
<p>Si algo falla, el encabezado te dirá el motivo y qué comando usar.</p>
</div>
""")


# =====================================================
# GUÍAS DE COMANDOS (listados de ejemplo)
# =====================================================

def lista_comandos_voz():
    bloques = ""
    for titulo, ejemplos in COMANDOS_VOZ:
        chips = "".join(f"<span class='cmd'>{e}</span>" for e in ejemplos)
        bloques += (
            f"<div class='cmd-grupo'><div class='cmd-titulo'>{titulo}</div>"
            f"{chips}</div>"
        )
    html(bloques)


def lista_gestos():
    filas = "".join(
        f"<div class='gesto'><b>{e}</b><div>{n}<br><span>{a}</span></div></div>"
        for e, n, a in GESTOS
    )
    html(f"<div class='cmd-grupo'><div class='cmd-titulo'>GESTOS DISPONIBLES</div>{filas}</div>")


# =====================================================
# PANEL DE ESTADO (telemetría real del ESP32)
# =====================================================

def _barra(valor, color):
    v = max(0, min(100, valor))
    return f"<div class='barra'><i style='width:{v}%;background:{color}'></i></div>"


@st.fragment(run_every=1)
def estado():

    S, client = nucleo()
    procesar_eventos(S, client)

    t = S["tele"]

    if not t:
        st.warning(
            "Esperando telemetría del ESP32. Abre el proyecto en Wokwi "
            "y pulsa ▶ para iniciar la simulación."
        )
    else:
        temp = float(t.get("temp", 0) or 0)
        comb = float(t.get("combustible", 0) or 0)
        dist = float(t.get("distancia", 0) or 0)
        mot = float(t.get("motores", 0) or 0)
        abierta = float(t.get("compuerta", 0) or 0) > 0
        nivel = nivel_alerta(t)

        c_temp = "c-bad" if temp > 30 else "c-ok"
        c_comb = "c-warn" if comb < 30 else "c-ok"
        col_comb = "#ffd400" if comb < 30 else "#2dffa0"
        col_temp = "#ff4d6a" if temp > 30 else "#00eaff"

        fichas = [
            chip("MISIÓN", t.get("mision", "—"),
                 "c-ok" if t.get("mision") == "EN VUELO"
                 else "c-bad" if t.get("mision") == "ABORTADO" else "c-info"),
            chip("ESCUDOS", "ACTIVOS" if t.get("escudos") else "INACTIVOS",
                 "c-ok" if t.get("escudos") else "c-off"),
            chip("COMPUERTA", "ABIERTA" if abierta else "CERRADA",
                 "c-warn" if abierta else "c-ok"),
            chip("ALERTA",
                 {"NORMAL": "NORMAL", "ROJA": "ROJA", "EXTREMA": "ROJA EXTREMA"}[nivel],
                 "c-ok" if nivel == "NORMAL" else "c-bad"),
            f"<div class='chip {c_comb}'><span class='chip-l'>COMBUSTIBLE</span>"
            f"<span class='chip-v'>{comb:.0f} %</span>{_barra(comb, col_comb)}</div>",
            f"<div class='chip {c_temp}'><span class='chip-l'>REACTOR</span>"
            f"<span class='chip-v'>{temp:.1f} °C</span>{_barra(temp * 100 / 60, col_temp)}</div>",
            f"<div class='chip c-info'><span class='chip-l'>MOTORES</span>"
            f"<span class='chip-v'>{mot:.0f} %</span>{_barra(mot, '#00eaff')}</div>",
            chip("RADAR", f"{dist:.0f} cm", "c-info"),
        ]

        html("<div class='rejilla'>" + "".join(fichas) + "</div>")

        if t.get("meteoritos"):
            st.warning("☄️ Meteoritos detectados (reactor > 30 °C). Di «activar escudos».")

        if t.get("emergencia"):
            st.error("🚨 Emergencia activa (botón de Wokwi o alerta extrema).")

        if t.get("motivo"):
            st.warning("📋 " + str(t["motivo"]))

        if S["ultima_telemetria"] is not None:
            st.caption(
                f"Última telemetría hace {time.time() - S['ultima_telemetria']:.1f} s"
            )

    st.caption("🎧 Entrada reconocida: " + str(S["oido"]))

    st.markdown(
        f"<div class='resp'>{S['resp']}</div>",
        unsafe_allow_html=True
    )

    st.caption("BITÁCORA")

    st.code("\n".join(S["log"]) or "Esperando eventos...")
