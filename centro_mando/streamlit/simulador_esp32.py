# Simula el ESP32 de Wokwi. Uso: python simulador_esp32.py
# Extra de prueba: publica {"temp":35} en <PREFIJO>/comandos para simular el DHT22.
import json, time
import paho.mqtt.client as mqtt

P = "NaveEspacial2026"          # MISMO prefijo que core.py y sketch.ino
E = dict(temp=25.0, combustible=80, distancia=200, emergencia=False, escudos=False,
         compuerta=0, motores=0, alertaMan=False, vuelo=False, mision="PLATAFORMA", motivo="")

def telemetria():
    met = E["temp"] > 30 and not E["escudos"]
    return dict(temp=E["temp"], combustible=E["combustible"], distancia=E["distancia"],
                emergencia=E["emergencia"], escudos=E["escudos"], meteoritos=met,
                compuerta=E["compuerta"], motores=E["motores"],
                alerta=E["alertaMan"] or met or E["emergencia"],
                mision=E["mision"], motivo=E["motivo"])

def despegar(ir):
    E["motivo"] = ""
    if not ir:
        E.update(vuelo=False, motores=0, mision="ABORTADO", motivo="Mision abortada"); return
    if not E["escudos"]: E["motivo"] = "Escudos desactivados"
    elif E["compuerta"] > 0: E["motivo"] = "Compuerta abierta"
    elif E["combustible"] < 30: E["motivo"] = "Combustible bajo"
    if E["motivo"]: E["mision"] = "ABORTADO"; return
    E.update(vuelo=True, motores=100, mision="EN VUELO")

def on_connect(c, u, f, rc):
    c.subscribe(P + "/comandos"); print("Simulador conectado, rc =", rc)

def on_message(c, u, m):
    try: d = json.loads(m.payload)
    except Exception: return
    print("Llego:", d)
    if "escudos" in d: E["escudos"] = bool(d["escudos"])
    if "alerta" in d: E["alertaMan"] = bool(d["alerta"])
    if "motores" in d: E["motores"] = max(0, min(100, int(d["motores"])))
    if "compuerta" in d and not E["vuelo"]: E["compuerta"] = int(d["compuerta"])
    if "despegue" in d: despegar(bool(d["despegue"]))
    if "temp" in d: E["temp"] = float(d["temp"])            # solo en el simulador
    if "emergencia" in d: E["emergencia"] = bool(d["emergencia"])  # solo en el simulador
    c.publish(P + "/telemetria", json.dumps(telemetria()))

c = mqtt.Client(); c.on_connect = on_connect; c.on_message = on_message
c.connect("broker.hivemq.com", 1883); c.loop_start()
while True:
    c.publish(P + "/telemetria", json.dumps(telemetria())); time.sleep(1)
