# 🚀 Centro de Mando Galáctico

Interfaz multimodal (voz y gestos) en **Streamlit** para controlar una nave espacial simulada en **Wokwi** (ESP32) por **MQTT**.
Con la temperatura del reactor por encima de 30 °C aparecen meteoritos en el visor; al activar los escudos desaparecen y se apaga la alerta.

## Estructura
- `Inicio.py`, `pages/`, `utils/`: app Streamlit (Puente de Mando por voz, Sala de Máquinas por gestos).
- `web/`: animación del visor y captura de voz/gestos (Web Speech API y MediaPipe).
- `wokwi/`: `sketch.ino`, `diagram.json`, `libraries.txt` (ESP32, DHT22, servo, LEDs, buzzer, HC-SR04).
- `simulador_esp32.py`: simula el ESP32 para probar sin Wokwi.

## Ejecutar
```
pip install -r requirements.txt
streamlit run Inicio.py
```
Opcional (sin Wokwi): `python simulador_esp32.py`

## MQTT (broker.hivemq.com:1883)
`NaveEspacial2026/comandos` (app → ESP32) · `NaveEspacial2026/telemetria` (ESP32 → app) · `NaveEspacial2026/entrada` (voz y gestos)

Comandos de voz: activar escudos · abrir/cerrar compuerta · alerta roja · iniciar despegue · abortar misión.
Gestos: 👍 escudos · 🤘 despegue · 🖐 compuerta · ✊ motores 0 % · 1-4 dedos = 25-100 %.
