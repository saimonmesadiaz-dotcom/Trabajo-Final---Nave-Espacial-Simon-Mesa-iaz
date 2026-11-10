// Librería: Sketch > Import Library > Manage Libraries > "MQTT" (Joel Gaehwiler)
// Voz y gestos llegan desde web/captura.html (modo voz / gestos) por MQTT: topic <P>/entrada
import mqtt.*;
MQTTClient cl;
String P = "nave_CAMBIA_2026";
float temp, comb, dist, motores, cohete = 0;
boolean escudos, meteoritos, emerg, alerta;
int compuerta;
String mision = "PLATAFORMA", motivo = "", oido = "-", resp = "Esperando ordenes", entrada = "";
float[][] est = new float[120][3];
ArrayList<float[]> met = new ArrayList<float[]>();
PFont f;

void setup() {
  size(1000, 600);
  f = createFont("Orbitron", 18, true);   // instala Orbitron; si no, usa fuente por defecto
  for (int i = 0; i < est.length; i++) { est[i][0] = random(width); est[i][1] = random(height); est[i][2] = random(TWO_PI); }
  cl = new MQTTClient(this);
  cl.connect("mqtt://broker.hivemq.com:1883", "proc_" + int(random(99999)));
}

void clientConnected() { cl.subscribe(P + "/telemetria"); cl.subscribe(P + "/entrada"); }

void draw() {
  background(5, 7, 15); textFont(f); noStroke();
  for (float[] s : est) { fill(255, 120 + 120 * sin(frameCount * 0.04 + s[2])); rect(s[0], s[1], 2, 2); }
  if (meteoritos) { if (frameCount % 12 == 0) { float x = random(width); met.add(new float[]{x, -20, (width/2 - x)/90, 450/90.0}); } }
  else met.clear();
  for (int i = met.size() - 1; i >= 0; i--) {
    float[] m = met.get(i); m[0] += m[2]; m[1] += m[3];
    stroke(255, 138, 0); strokeWeight(4); line(m[0], m[1], m[0] - m[2]*6, m[1] - m[3]*6);
    noStroke(); fill(255, 180, 70); ellipse(m[0], m[1], 18, 18);
    if (m[1] > 430) met.remove(i);
  }
  cohete = mision.equals("EN VUELO") ? min(cohete + 3, 300) : max(cohete - 6, 0);
  float x = width/2, y = 440 - cohete;
  if (motores > 0) { fill(255, 138, 0); triangle(x-14, y+50, x+14, y+50, x, y + 50 + motores*0.6 + random(12)); }
  fill(223, 233, 255); rect(x-20, y-40, 40, 90); triangle(x-20, y-40, x, y-90, x+20, y-40);
  fill(255, 43, 214); rect(x-34, y+25, 14, 30); rect(x+20, y+25, 14, 30);
  fill(compuerta > 0 ? color(0) : color(0, 245, 255)); rect(x-9, y-8, 18, 30);
  if (escudos) {   // halo alrededor de toda la ventana
    noFill();
    for (int i = 0; i < 6; i++) { stroke(0, 245, 255, 150 - i*22); strokeWeight(4 + i*3); rect(6, 6, width-12, height-12, 20); }
    stroke(0, 245, 255); strokeWeight(3); ellipse(x, y, 190, 230);
  }
  noStroke(); textAlign(LEFT);
  fill(temp > 30 ? color(255, 59, 59) : color(0, 245, 255)); text("REACTOR " + nf(temp, 0, 1) + " C", 20, 30);
  fill(comb < 30 ? color(255, 212, 0) : color(0, 245, 255)); text("COMBUSTIBLE " + int(comb) + "%", 20, 58);
  fill(0, 245, 255); text("RADAR " + int(dist) + " cm", 20, 86);
  fill(255, 43, 214); textAlign(RIGHT); text("MISION: " + mision, width-20, 30);
  fill(255, 212, 0); text(motivo, width-20, 58); textAlign(LEFT);
  boolean on = alerta && (frameCount / 15) % 2 == 0;   // boton ALERTA titilante
  fill(on ? color(255, 31, 61) : color(58, 10, 20)); rect(760, 520, 200, 56, 10);
  fill(255); text("ALERTA", 815, 556);
  fill(0, 245, 255); text("> " + entrada, 20, 540);
  fill(255, 43, 214); text(resp, 20, 568); fill(150); text("oi: " + oido, 20, 512);
}

void messageReceived(String topic, byte[] payload) {
  JSONObject j = parseJSONObject(new String(payload));
  if (j == null) return;
  if (topic.endsWith("telemetria")) {
    temp = j.getFloat("temp"); comb = j.getFloat("combustible"); dist = j.getFloat("distancia");
    motores = j.getFloat("motores"); compuerta = j.getInt("compuerta");
    escudos = j.getBoolean("escudos"); meteoritos = j.getBoolean("meteoritos");
    emerg = j.getBoolean("emergencia"); alerta = j.getBoolean("alerta");
    mision = j.getString("mision"); motivo = j.getString("motivo");
  } else if (j.getString("tipo").equals("voz")) voz(j.getString("texto"));
  else gesto(j);
}

void cmd(String json, String r) { cl.publish(P + "/comandos", json); resp = r; }

void voz(String t) {
  t = t.toLowerCase(); oido = t;
  boolean off = t.contains("desactiv") || t.contains("apag") || t.contains("cerr");
  if (t.contains("abort")) cmd("{\"despegue\":false}", "Mision abortada");
  else if (t.contains("despeg")) cmd("{\"despegue\":true}", "Verificando despegue...");
  else if (t.contains("escudo")) cmd("{\"escudos\":" + !off + "}", off ? "Escudos desactivados" : "Escudos activados, capitan");
  else if (t.contains("alerta")) cmd("{\"alerta\":" + !off + "}", off ? "Alerta apagada" : "Alerta roja");
  else if (t.contains("compuerta") || t.contains("puerta")) cmd("{\"compuerta\":" + (off ? 0 : 90) + "}", off ? "Cerrando compuerta" : "Abriendo compuerta");
  else if (t.contains("motor")) cmd("{\"motores\":" + (off ? 0 : 80) + "}", off ? "Motores apagados" : "Motores al 80%");
  else resp = "Comando no reconocido";
}

void gesto(JSONObject j) {
  String g = j.getString("gesto"); oido = "gesto: " + g;
  if (g.equals("escudos")) cmd("{\"escudos\":true}", "Escudos activados (gesto)");
  else if (g.equals("despegue")) cmd("{\"despegue\":true}", "Verificando despegue (gesto)");
  else if (g.equals("compuerta")) cmd("{\"compuerta\":" + (compuerta > 0 ? 0 : 90) + "}", "Compuerta en movimiento");
  else if (g.equals("motores")) { int v = j.getInt("valor"); cmd("{\"motores\":" + v + "}", "Motores al " + v + "%"); }
}

void keyPressed() {   // plan B por texto
  if (key == ENTER || key == RETURN) { voz(entrada); entrada = ""; }
  else if (key == BACKSPACE) { if (entrada.length() > 0) entrada = entrada.substring(0, entrada.length() - 1); }
  else if (key != CODED) entrada += key;
}

void mousePressed() { if (mouseX > 760 && mouseX < 960 && mouseY > 520 && mouseY < 576) cmd("{\"alerta\":" + !alerta + "}", "Alerta alternada"); }
