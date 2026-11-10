import json, time
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import paho.mqtt.client as mqtt

P = "nave_CAMBIA_2026"            # igual que en Wokwi y web/
WEB = Path(__file__).resolve().parents[2] / "web"

def interpretar(t):
    t = t.lower(); off = any(w in t for w in ("desactiv", "apag", "cerr"))
    if "abort" in t: return {"despegue": False}, "Misión abortada"
    if "despeg" in t: return {"despegue": True}, "Verificando despegue..."
    if "escudo" in t: return {"escudos": not off}, "Escudos " + ("desactivados" if off else "activados, capitán")
    if "alerta" in t: return {"alerta": not off}, "Alerta " + ("apagada" if off else "roja activada")
    if "compuerta" in t or "puerta" in t: return {"compuerta": 0 if off else 90}, "Compuerta " + ("cerrándose" if off else "abriéndose")
    if "motor" in t: return {"motores": 0 if off else 80}, "Motores " + ("apagados" if off else "al 80 %")
    return None, "Comando no reconocido"

def desde_gesto(e, tele):
    g = e.get("gesto")
    if g == "escudos": return {"escudos": True}, "Escudos activados (gesto 👍)"
    if g == "despegue": return {"despegue": True}, "Verificando despegue (gesto 🤘)"
    if g == "compuerta":
        a = 0 if tele.get("compuerta", 0) > 0 else 90
        return {"compuerta": a}, "Compuerta " + ("cerrándose" if a == 0 else "abriéndose")
    if g == "motores": v = int(e.get("valor") or 0); return {"motores": v}, f"Motores al {v} %"
    return None, "Gesto desconocido"

def registrar(S, c, cmd, resp):
    if cmd: c.publish(P + "/comandos", json.dumps(cmd))
    S["resp"] = resp
    S["log"] = [time.strftime("%H:%M:%S") + " · " + resp] + S["log"][:7]

@st.cache_resource
def nucleo():
    S = {"tele": {}, "log": [], "oido": "—", "resp": "Esperando órdenes"}
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client()
    c.on_connect = lambda cl, u, f, rc: cl.subscribe([(P + "/telemetria", 0), (P + "/entrada", 0)])
    def on_message(cl, u, m):
        try: d = json.loads(m.payload)
        except Exception: return
        if m.topic.endswith("telemetria"): S["tele"].update(d); return
        if d.get("tipo") == "voz": S["oido"] = d["texto"]; cmd, resp = interpretar(d["texto"])
        else: S["oido"] = "gesto: " + str(d.get("gesto")); cmd, resp = desde_gesto(d, S["tele"])
        registrar(S, cl, cmd, resp)
    c.on_message = on_message
    c.connect("broker.hivemq.com", 1883); c.loop_start()
    return S, c

def ejecutar(texto):
    S, c = nucleo(); S["oido"] = texto; cmd, resp = interpretar(texto); registrar(S, c, cmd, resp)

def enviar(**cmd):
    S, c = nucleo(); registrar(S, c, cmd, "Orden manual: " + json.dumps(cmd))

def visual(vista="ventana"):
    html = (WEB / "visual.html").read_text().replace("__PREFIJO__", P).replace("__VISTA__", vista)
    components.html(html, height=460)

def captura(modo, h=480):
    components.html((WEB / "captura.html").read_text().replace("__PREFIJO__", P).replace("__MODO__", modo), height=h)

def estilos():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap');
    .stApp{background:linear-gradient(160deg,#05070f,#1a0b2e);color:#d7f8ff}
    h1,h2,h3,h4,[data-testid=stMetricValue]{font-family:'Orbitron',sans-serif!important;color:#00f5ff!important;text-shadow:0 0 12px #00f5ff88}
    [data-testid=stMetric]{border:1px solid #00f5ff66;border-radius:12px;padding:10px;box-shadow:0 0 14px #00f5ff33}
    .resp{border-left:4px solid #ff2bd6;padding:8px 14px;background:#ff2bd610;border-radius:6px}
    [data-testid=stSidebar]{background:linear-gradient(180deg,#070a18,#150a2a);border-right:1px solid #00f5ff33}
    [data-testid=stSidebarNav] a,[data-testid=stSidebarNavLink]{border-radius:14px;margin:5px 0;font-family:'Orbitron',sans-serif;letter-spacing:.6px;transition:.2s}
    [data-testid=stSidebarNav] a:hover,[data-testid=stSidebarNavLink]:hover{background:#00f5ff18;box-shadow:0 0 14px #00f5ff44}
    [data-testid=stSidebarNav] a[aria-current=page],[data-testid=stSidebarNavLink][aria-current=page]{background:linear-gradient(90deg,#00f5ff30,#ff2bd630);border:1px solid #00f5ff88;box-shadow:0 0 16px #00f5ff44}
    .marca{font-family:'Orbitron',sans-serif;text-align:center;padding:14px 8px;margin-bottom:6px;border-radius:16px;border:1px solid #ff2bd666;background:radial-gradient(circle at 50% 0,#ff2bd622,transparent)}
    .marca b{font-size:22px;color:#00f5ff;text-shadow:0 0 14px #00f5ff}.marca span{font-size:11px;color:#9fb6d8;letter-spacing:2px}
    .chip{font-family:'Orbitron',sans-serif;font-size:12px;border:1px solid #00f5ff55;border-radius:999px;padding:6px 12px;margin:4px 0;background:#00f5ff0d}
    </style>""", unsafe_allow_html=True)

@st.fragment(run_every=2)
def mini():
    S, _ = nucleo(); t = S["tele"]
    st.markdown(f"<div class='chip'>{'🟢 Nave en línea' if t else '🔴 Sin telemetría'}</div>", unsafe_allow_html=True)
    if t:
        st.markdown(f"<div class='chip'>🎯 {t.get('mision', '—')}</div><div class='chip'>🌡️ Reactor {t.get('temp', 0):.1f} °C</div>"
                    f"<div class='chip'>{'🛡️ Escudos ON' if t.get('escudos') else '⚪ Escudos OFF'}</div>"
                    f"<div class='chip'>{'🔴 ALERTA' if t.get('alerta') else '✅ Sin alertas'}</div>", unsafe_allow_html=True)

def barra_lateral():
    with st.sidebar:
        st.markdown("<div class='marca'>🛰️ <b>ORIÓN</b><br><span>CENTRO DE MANDO</span></div>", unsafe_allow_html=True)
        mini()

@st.fragment(run_every=1)
def estado():
    S, _ = nucleo(); t = S["tele"]
    if not t: st.warning("Sin telemetría: ¿está corriendo Wokwi y coincide el prefijo?")
    a, b = st.columns(2)
    a.metric("Misión", t.get("mision", "—")); b.metric("Reactor", f"{t.get('temp', 0):.1f} °C")
    a.metric("Escudos", "ON" if t.get("escudos") else "OFF"); b.metric("Compuerta", "ABIERTA" if t.get("compuerta", 0) > 0 else "CERRADA")
    a.metric("Combustible", f"{t.get('combustible', 0)} %"); b.metric("Alerta", "🔴 SÍ" if t.get("alerta") else "no")
    st.caption("Entendí: " + S["oido"]); st.markdown(f"<div class='resp'>{S['resp']}</div>", unsafe_allow_html=True)
    if t.get("motivo"): st.warning(t["motivo"])
    st.caption("Bitácora"); st.code("\n".join(S["log"]) or "—")
