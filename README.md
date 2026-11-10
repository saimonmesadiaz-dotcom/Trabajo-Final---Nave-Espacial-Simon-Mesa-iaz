# Trabajo-Final---Nave-Espacial-Simon-Mesa-Diaz
Centro de Mando Galáctico: interfaz multimodal (voz y gestos) en Streamlit y Processing para controlar una nave espacial simulada en Wokwi (ESP32) por MQTT.

# 🚀 Centro de Mando Galáctico

Simulación de robótica y astronomía con **control sin contacto**. El usuario es el
capitán de una nave espacial: prepara los sistemas, decide si despega o no, y
responde a los peligros del espacio (meteoritos, sobrecalentamiento, falta de
combustible y emergencias).

El proyecto combina una interfaz web (**Streamlit**) y una versión alternativa
(**Processing**) con un **ESP32 simulado en Wokwi**, conectados por **MQTT**.

## Interacción multimodal
- 🎙️ **Voz** (Puente de Mando): órdenes como "activar escudos" o "iniciar despegue".
- 🖐️ **Gestos** (Sala de Máquinas): control de motores y escudos con la mano, usando la cámara.
- ⌨️ Texto y controles manuales como respaldo.

## Qué ocurre en Wokwi
Con la temperatura del reactor (DHT22) por encima de 30 °C aparecen meteoritos en la
interfaz y titilan el LED rojo y el buzzer. Al activar los escudos, los meteoritos
desaparecen y se apaga la alerta. También se abren y cierran compuertas (servo) y se
verifica el despegue (escudos, compuerta cerrada y combustible suficiente).

## Tecnologías
Streamlit · Processing · ESP32 (Arduino C++) · Wokwi · MQTT (HiveMQ) · MediaPipe · Web Speech API

## Propósito
Es una simulación educativa y un modelo de interfaz para personas que necesitan dar
órdenes sin depender del tacto (movilidad reducida o manos ocupadas).

> Proyecto final de Interfaces Multimodales · Simón · 2026
