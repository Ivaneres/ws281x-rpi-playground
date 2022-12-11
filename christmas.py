import socket
import pickle
from tracemalloc import start
from turtle import color
from rpi_ws281x import PixelStrip, Color
import queue
import math
import schedule
import time
from datetime import datetime

LED_COUNT = 288       # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

PATTERN_STEP = 40
PATTERN_COLORS = ((255, 0, 0), (0, 255, 0))
ANIMATION_SECS = 3

print("Booting...")

def switch_on():
    print("Switching on!")
    color_counter = 0
    for t in range(ANIMATION_SECS * 10):
        for i in range(LED_COUNT):
            if (i % PATTERN_STEP) == 0:
                color_counter += 1
            if color_counter >= len(PATTERN_COLORS):
                color_counter = 0
            color = PATTERN_COLORS[color_counter] * (t / 10)
            strip.setPixelColor(i, Color(*color))
        strip.show()
        time.sleep(0.1)

def switch_off():
    print("Switching off.")
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
        
if datetime.now().time() > datetime(1970, 1, 1, 16, 30).time():
    switch_on()

schedule.every().day.at("16:30").do(switch_on)
schedule.every().day.at("00:00").do(switch_off)
while True:
    schedule.run_pending()
    time.sleep(1)
