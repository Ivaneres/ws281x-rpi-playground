import socket
import pickle
from tracemalloc import start
from turtle import color
from rpi_ws281x import PixelStrip, Color
import queue
import math

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

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

def rgbFromEnc(enc):
    b = enc & 255
    g = (enc >> 8) & 255
    r = (enc >> 16) & 255
    return r, g, b

def decode_tuple(s):
    return tuple(int(x) for x in s.split("|"))

def is_data(s):
    return "|" in s or str.isnumeric(s)

state = "wave"  # expects "wave" or "all"

while True:
    d, addr = sock.recvfrom(64)
    s = d.decode()
    if not is_data(s):
        state = s
        continue
    colour = decode_tuple(s)
    colour_obj = Color(*colour)
    total_len = strip.numPixels()
    if state == "wave":
        half_point = 190
        prev_pixels = strip.getPixels()
        step_size = 10
        l = 0
        while l < half_point - step_size:
            for j in range(step_size):
                strip.setPixelColor(l + j, prev_pixels[l + step_size])
            l += step_size
        l -= step_size
        for j in range(half_point - l):
            strip.setPixelColor(l + j, prev_pixels[half_point])
        r = total_len
        while r > half_point + step_size:
            for j in range(step_size):
                strip.setPixelColor(r - j, prev_pixels[r - step_size])
            r -= step_size
        r += step_size
        for j in range(r - half_point):
            strip.setPixelColor(r - j, prev_pixels[half_point])
        strip.setPixelColor(half_point, colour_obj)
    else:
        for i in range(total_len):
            strip.setPixelColor(i, colour_obj)
    strip.show()
