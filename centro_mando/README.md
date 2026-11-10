# Centro de Mando Galáctico
1. Mantén el mismo prefijo `NaveEspacial2026` en wokwi/sketch.ino, streamlit/utils/core.py y processing/nave_processing/nave_processing.pde. No lo cambies solo en uno de los archivos.
2. Wokwi: proyecto ESP32 nuevo, pega sketch.ino, diagram.json y libraries.txt. Ejecuta. Sube el DHT22 a >30 °C.
3. Streamlit: cd streamlit && pip install -r requirements.txt && streamlit run app.py
4. Processing: instala la librería MQTT, abre processing/nave_processing y ejecuta.
   Voz/gestos: cd web && python -m http.server 8000 -> http://localhost:8000/captura.html?modo=voz (o modo=gestos) &p=TU_PREFIJO en Chrome.
