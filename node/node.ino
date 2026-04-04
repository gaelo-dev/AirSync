/*
* Proyecto: AirSync
* Descripción: Nodo sensor para medición de la calidad del aire con conectividad WPA2-Enterprise.
* 
* CRÉDITOS:
* -----------------------------
* 1. Lógica del Sensor de polvo (GP2Y1010AU0F):
*    Autor: Mirko Pavleski (mircemk)
*    URL: https://create.arduino.cc/projecthub/mircemk/diy-air-quality-monitor-with-sharp-gp2y1010au0f-sensor-7b0262
* 
* 2. Conectividad WiFi WPA2-Enterprise:
*    Autor: Jeroen Beemster
*    URL: https://github.com/JeroenBeemster/ESP32-WPA2-enterprise
* 
* MODIFICACIONES Y ADAPTACIÓN:
* ----------------------------
* Desarrollado por: @gaelo-dev
* - Integración de la lógica de muestreo del sensor Sharp Optical Dust.
* - Implementación de la logica de conexion WiFi y envio de los datos con el stack de red del ESP32.
* - Ajuste de temporización (timing) para evitar interferencias entre el muestreo analógico y las tareas de red.
*/

#include "esp_eap_client.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "arduino_secrets.h"

// Pins & Constants
const int MEASURE_PIN = 27; // Pin analógico
const int LED_POWER = 26;     // Pin que activa el LED del sensor

// Timing para el sensor de polvo (según datasheet)
const int SAMPLING_TIME = 280;
const int DELTA_TIME = 40;
const int SLEEP_TIME = 9680;

// Configuración para el Deep Sleep
#define uS_TO_S 1000000ULL
RTC_DATA_ATTR int boot_count = 0;

// --- FUNCIONES DE OBTENCIÓN DE DATOS ---
float get_dust_density() {
    digitalWrite(LED_POWER, HIGH); // Encender LED del sensor
    delayMicroseconds(SAMPLING_TIME);

    float vo_measured = analogRead(MEASURE_PIN);

    delayMicroseconds(DELTA_TIME);
    digitalWrite(LED_POWER, LOW); // Apagar LED
    delayMicroseconds(SLEEP_TIME);

    // Conversión: ADC (12-bit en ESP32) -> Voltaje -> Densidad
    // 3.3V / 4095.0 es la resolución del ESP32. 
    // El factor 1.5 compensa la atenuación del divisor de tensión, restaurando el rango de 5V.
    float calc_voltage = (vo_measured * (3.3 / 4095.0)) * 1.5;

    // linear eqaution taken from http://www.howmuchsnow.com/arduino/airquality/
    // Chris Nafis (c) 2012
    float dust_density = 0.17 * calc_voltage * 1000 - 0.1;
    return (dust_density < 0) ? 0.00 : dust_density;
}

float get_gas_concentration() {
  return 0.0;
}

float get_temperature() {
  return 0.0;
}

float get_humidity() {
  return 0.0;
}

// --- LÓGICA DE TURNOS (SLOTTING) ---
uint32_t get_slot() {
    return (DEVICE_ID % SLEEP_SEC);
}

// --- LOGICA DE CONEXION WiFi Y ENVIO DE DATOS ---
void conn_wifi() {
    Serial.printf("Connecting to SSID: %s\n", SSID);
    
    WiFi.disconnect(true); 
    WiFi.mode(WIFI_STA);
    
    // WPA2 enterprise magic starts here
    esp_eap_client_set_identity((uint8_t *)EAP_ID, strlen(EAP_ID));
    esp_eap_client_set_username((uint8_t *)EAP_USERNAME, strlen(EAP_USERNAME));
    esp_eap_client_set_password((uint8_t *)EAP_PASSWORD, strlen(EAP_PASSWORD));
    
    esp_wifi_sta_enterprise_enable();
    // WPA2 enterprise magic ends here

    WiFi.begin(SSID);

    int retry_count = 0;
    const int MAX_RETRIES = 40; // 40 * 500ms = 20s
    while (WiFi.status() != WL_CONNECTED && retry_count < MAX_RETRIES) {
        delay(500);
        Serial.print(".");
        retry_count++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F("\nWiFi connected!"));
        Serial.print(F("IP address: "));
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(F("\nFailed to connect."));
    }
}

void post_data(float temp, float humidity, float pm10, float gas) {
    if (WiFi.status() != WL_CONNECTED) return;
    HTTPClient http;

    // Configurar la petición
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-KEY", SECRET_API_KEY);

    // Construir el cuerpo JSON 
    StaticJsonDocument<200> doc;
    doc["device_id"] = DEVICE_ID; 
    doc["temp"]      = temp;
    doc["humidity"]  = humidity;
    doc["pm10"]      = pm10;
    doc["gas"]       = gas;

    String json_output;
    serializeJson(doc, json_output);

    // Ejecutar petición POST
    Serial.println(F("Post data -> API"));
    int http_code = http.POST(json_output);

    // Feedback y cierre
    if (http_code > 0) {
        Serial.printf("API Status: %d\n", http_code);
        if (http_code == HTTP_CODE_OK || http_code == HTTP_CODE_CREATED) {
            Serial.println(F("API: OK!"));
        }
    } else {
        // Si es menor a 0, el problema es el WiFi o el Cliente HTTP
        Serial.printf(F("[HTTP] Error: %s\n"), http.errorToString(http_code).c_str());
    }
    
    http.end();
}

void setup() {
    Serial.begin(115200);
    boot_count++;

    // Configuración inicial de pines
    pinMode(LED_POWER, OUTPUT);
    digitalWrite(LED_POWER, LOW);

    // Escalonamiento inicial (Solo en el primer arranque real)
    if (boot_count == 1) {
        uint32_t wait_ms = get_slot() * 1000;
        Serial.printf("Cold Boot: Waiting %u ms for my slot...\n", wait_ms);
        delay(wait_ms);
    }

    // Obtención de datos 
    float dust = get_dust_density();
    float gc = get_gas_concentration();
    float temp = get_temperature();
    float humidity = get_humidity();

    Serial.printf("Dust Density: %.2f mg/m3\n", dust);

    // Conexión WiFi y el envío de datos a la API
    conn_wifi();
    post_data(temp, humidity, dust, gc);

    // Ir a dormir por 3 minutos
    Serial.println(F("Cycle finished. Deep sleep..."));
    esp_sleep_enable_timer_wakeup(SLEEP_SEC * uS_TO_S);
    esp_deep_sleep_start();
}

void loop() {
    // Vacío
}
