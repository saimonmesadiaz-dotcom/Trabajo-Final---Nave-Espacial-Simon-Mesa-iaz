#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32Servo.h>

const char* PREFIJO = "nave_CAMBIA_2026";   // igual en todos los archivos
#define P_DHT 15
#define P_POT 34
#define P_TRIG 5
#define P_ECHO 18
#define P_BTN 4
#define P_AZUL 25    // escudos
#define P_ROJO 26    // alerta (titila)
#define P_VERDE 27   // motores PWM
#define P_BUZ 14
#define P_SERVO 13   // compuerta

WiFiClient wifi; PubSubClient mqtt(wifi);
DHT dht(P_DHT, DHT22); Servo servo;
String tCmd, tTel;
float temp = 25; int comb = 0, dist = 0, compuerta = 0, motores = 0;
bool escudos = false, alertaMan = false, vuelo = false, emerg = false, emergPrev = false, parpadeo = false;
String mision = "PLATAFORMA", motivo = "";
unsigned long tTele = 0, tParp = 0;

bool meteoritos() { return temp > 30 && !escudos; }      // regla de supervivencia
bool alertaActiva() { return alertaMan || meteoritos() || emerg; }

void publicar() {
  JsonDocument d;
  d["temp"] = temp; d["combustible"] = comb; d["distancia"] = dist;
  d["emergencia"] = emerg; d["escudos"] = escudos; d["meteoritos"] = meteoritos();
  d["compuerta"] = compuerta; d["motores"] = motores; d["alerta"] = alertaActiva();
  d["mision"] = mision; d["motivo"] = motivo;
  char buf[400]; serializeJson(d, buf);
  mqtt.publish(tTel.c_str(), buf);
}

void despegar(bool ir) {
  motivo = "";
  if (!ir) { vuelo = false; motores = 0; mision = "ABORTADO"; motivo = "Mision abortada"; return; }
  if (!escudos) motivo = "Escudos desactivados";
  else if (compuerta > 0) motivo = "Compuerta abierta";
  else if (comb < 30) motivo = "Combustible bajo";
  if (motivo != "") { mision = "ABORTADO"; return; }
  vuelo = true; motores = 100; mision = "EN VUELO";
}

void onMsg(char* t, byte* p, unsigned int n) {
  JsonDocument d;
  if (deserializeJson(d, p, n)) return;
  if (!d["escudos"].isNull()) escudos = d["escudos"];
  if (!d["alerta"].isNull()) alertaMan = d["alerta"];
  if (!d["motores"].isNull()) motores = constrain((int)d["motores"], 0, 100);
  if (!d["compuerta"].isNull() && !vuelo) compuerta = d["compuerta"];
  if (!d["despegue"].isNull()) despegar(d["despegue"]);
  servo.write(compuerta);
  publicar();
}

void conectar() {
  while (!mqtt.connected()) {
    if (mqtt.connect(("esp32_" + String(random(99999))).c_str())) mqtt.subscribe(tCmd.c_str());
    else delay(1000);
  }
}

void leer() {
  float t = dht.readTemperature(); if (!isnan(t)) temp = t;
  comb = map(analogRead(P_POT), 0, 4095, 0, 100);
  digitalWrite(P_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(P_TRIG, HIGH); delayMicroseconds(10); digitalWrite(P_TRIG, LOW);
  long us = pulseIn(P_ECHO, HIGH, 30000);
  dist = us ? us * 0.034 / 2 : 400;
}

void setup() {
  pinMode(P_AZUL, OUTPUT); pinMode(P_ROJO, OUTPUT); pinMode(P_VERDE, OUTPUT);
  pinMode(P_TRIG, OUTPUT); pinMode(P_ECHO, INPUT); pinMode(P_BTN, INPUT_PULLUP);
  dht.begin(); servo.attach(P_SERVO); servo.write(0);
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(200);
  tCmd = String(PREFIJO) + "/comandos"; tTel = String(PREFIJO) + "/telemetria";
  mqtt.setServer("broker.hivemq.com", 1883); mqtt.setBufferSize(512); mqtt.setCallback(onMsg);
}

void loop() {
  if (!mqtt.connected()) conectar();
  mqtt.loop();
  unsigned long ms = millis();
  emerg = digitalRead(P_BTN) == LOW;
  if (emerg != emergPrev) { emergPrev = emerg; publicar(); }
  if (ms - tTele > 1000) { tTele = ms; leer(); publicar(); }
  if (ms - tParp > 250) { tParp = ms; parpadeo = !parpadeo; }
  bool a = alertaActiva();
  digitalWrite(P_ROJO, a && parpadeo);               // LED rojo titila mientras haya amenaza
  if (a && parpadeo) tone(P_BUZ, 880); else noTone(P_BUZ);
  digitalWrite(P_AZUL, escudos);                     // escudos => deja de titilar y se apaga el rojo
  analogWrite(P_VERDE, motores * 255 / 100);
}
