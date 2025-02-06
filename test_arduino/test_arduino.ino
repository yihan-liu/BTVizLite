const int num_values = 10;

void setup()
{
    Serial.begin(9600);
    while (!Serial);
    randomSeed(analogRead(A0));
}

void loop()
{
    if (Serial.available() > 0)
    {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.equalsIgnoreCase("on"))
            digitalWrite(LED_BUILTIN, HIGH);
        else if (command.equalsIgnoreCase("off"))
            digitalWrite(LED_BUILTIN, LOW);
    }

    for (int i = 0; i < num_values; i++)
    {
        int rand_value = random(0, 1000);
        Serial.print(rand_value);
        if (i < num_values - 1)
            Serial.print(",");
    }

    Serial.println();
    delay(200);
}
