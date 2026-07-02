#include <Arduino.h>
#include <Wire.h>

#define SDA_PIN 21
#define SCL_PIN 22

void scanI2C()
{
    uint8_t count = 0;

    Serial.println("--------------------------------");
    Serial.println("Scanning I2C bus...");

    for (uint8_t address = 1; address < 127; address++)
    {
        Wire.beginTransmission(address);
        uint8_t error = Wire.endTransmission();

        if (error == 0)
        {
            Serial.print("Device found at 0x");

            if (address < 16)
                Serial.print("0");

            Serial.println(address, HEX);

            count++;
        }
        else if (error == 4)
        {
            Serial.print("Unknown error at 0x");

            if (address < 16)
                Serial.print("0");

            Serial.println(address, HEX);
        }
    }

    Serial.print("Total devices: ");
    Serial.println(count);

    Serial.println("--------------------------------");
}

void setup()
{
    Serial.begin(115200);
    delay(2000);

    Wire.begin(SDA_PIN, SCL_PIN);
    Wire.setClock(100000);

    Serial.println("ESP32 I2C Scanner");
}

void loop()
{
    scanI2C();
    delay(2000);
}