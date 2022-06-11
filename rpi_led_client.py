from concurrent.futures import thread
import socket
import pickle
from scipy import signal
from scipy.io import wavfile
import time
from matplotlib import pyplot as plt
import numpy as np
import sys
import pyaudio
import struct
from spotify_integration import SpotifyPlayingMonitor
from colorthief import ColorThief
import requests
import io
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
from sty import Style, RgbFg, fg

UDP_IP = "192.168.1.126"
UDP_PORT = 5005
 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = int(44100 / 20)

SPOTIFY_ENABLED = True
SPOTIFY_CHECK_RATE = 3

p = pyaudio.PyAudio()

print("====================== AUDIO DEVICES ======================")
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print((i,dev['name'],dev['maxInputChannels']))
 
# start Recording
stream = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK, input_device_index=10)

frequency_bins = [
    0,
    50,
    75,
    125,
    250,
    500,
    1000,
    2000,
    4000,
    6000,
    10000,
    20000
]

# default colours
colour_gradient = np.array([[0, 255, 0], [125, 255, 125], [255, 255, 255]])

def fetch_album_colours(album_art_url):
    response = requests.get(album_art_url)
    if response.status_code != 200:
        raise ConnectionError("Failed to fetch album art")
    ct = ColorThief(io.BytesIO(response.content))
    colours = ct.get_palette(color_count=5, quality=1)
    colours = sorted(filter(lambda c: sum(c) > 100, colours), key=lambda x: max(x) - min(x), reverse=True)
    brightest_colour = colours[0]
    colour_differences = [sum(map(lambda x, y: abs(x - y), brightest_colour, c)) for c in colours[1:]]
    brightness_sort = [x for x, _ in sorted(zip(colours[1:], colour_differences), key=lambda pair: pair[1], reverse=True)]
    print(brightest_colour)
    print(colour_differences)
    print(colours[1:])
    return [brightest_colour] + brightness_sort

def spotify_monitor(colours_list, c_id, c_sec, redir):
    print("Starting spotify monitor thread")
    original_colours = colours_list.copy()
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="user-read-currently-playing", 
        client_id=c_id, 
        client_secret=c_sec, 
        redirect_uri=redir
    ))
    prev_track_id = None
    while True:
        try:
            track = sp.current_user_playing_track()
        except requests.exceptions.ConnectionError:
            print("Spotify API error")
            time.sleep(SPOTIFY_CHECK_RATE)
            continue
        if track is None:
            if not (colours_list == original_colours).all():
                for i in range(colours_list.shape[0]):
                    colours_list[i] = original_colours[i]
            time.sleep(SPOTIFY_CHECK_RATE)
            continue
        if track["item"] is None:
            time.sleep(SPOTIFY_CHECK_RATE)
            continue
        track_id = track["item"]["id"]
        art_url = track["item"]["album"]["images"][0]["url"]
        if track_id != prev_track_id:
            colours = fetch_album_colours(art_url)
            for col in colours:
                col_str = str(col)
                print(f"{col}{' ' * (16 - len(col_str))}{fg(*col)}████████████████████████████████████████████{fg.rs}")
            print()
            colours_list[0] = colours[0]
            colours_list[2] = colours[1]
            colours_list[1] = ((colours_list[0] + colours_list[2]) / 2).astype(int)
            # for i in range(colours_list.shape[0]):
            #     colours_list[i] = colours[i]
        prev_track_id = track_id
        time.sleep(SPOTIFY_CHECK_RATE)
        
if SPOTIFY_ENABLED:
    load_dotenv("spotify.env")
    t = threading.Thread(target=spotify_monitor, args=(
        colour_gradient,
        os.environ.get("SPOTIFY_CLIENT_ID"),
        os.environ.get("SPOTIFY_CLIENT_SECRET"),
        os.environ.get("SPOTIPY_REDIRECT_URI")
    ))
    t.start()

def encode_tuple(tup):
    return "|".join(map(str, tup)).encode()

def softmax(x):
    e = np.exp(x)
    return e / e.sum()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto("wave".encode(), (UDP_IP, UDP_PORT))

while True:
    data = stream.read(CHUNK)
    data = np.frombuffer(data, dtype=np.int16)

    fourier = np.abs(np.fft.rfft(data))
    # p = np.where(fourier > 0, np.log(fourier), 0)
    p = fourier
    freqs = np.fft.rfftfreq(data.size, d=1./RATE)
    
    # plt.plot(freqs, p)
    # plt.show()
    
    p[freqs < 150] *= 2

    bass = np.sum(p[freqs < 150])
    mids = np.sum(p[(freqs > 150) & (freqs < 3000)])
    treble = np.sum(p[freqs > 3000])
    all_freqs = np.sum(p)
    
    if all_freqs != 0:
        bass_ratio = bass / all_freqs
        mids_ratio = mids / all_freqs
        treble_ratio = treble / all_freqs
        
        ratios = np.array([bass_ratio, mids_ratio, treble_ratio])
        # print("Ratios:", (ratios * 100).astype(int))
        sm = softmax(ratios * 5)
        # print("Softmax:", (sm * 100).astype(int))
        ratios = sm
        colour = np.nan_to_num(ratios.reshape(-1, 1) * colour_gradient).sum(axis=0)
    else:
        colour = np.array([0, 0, 0])
    
    rms_amp = (np.sqrt(np.mean((data * 1./32768) ** 2)) / 0.6).item()
    if rms_amp > 1.0:
        rms_amp = 1.0
    # log_rms = 20 * np.log10(rms_amp)
    # rms_amp = np.tanh(1.3 * rms_amp)
    # print(rms_amp, type(rms_amp))

    scaled_colour = rms_amp * colour
    
    # if scaled_colour[1:3].sum() > 130:
    #     scaled_colour -= [0, 30, 30]
    #     scaled_colour[scaled_colour < 0] = 0
    
    int_colour_tuple = tuple(scaled_colour.astype(int))
    int_colour_tuple = tuple(x.item() for x in int_colour_tuple)
    
    # print(sys.getsizeof(int_colour_tuple))
    # print(type(int_colour_tuple), type(int_colour_tuple[0]))

    # sock.sendto(pickle.dumps(frequencies.tolist()), (UDP_IP, UDP_PORT))
    sock.sendto(encode_tuple(int_colour_tuple), (UDP_IP, UDP_PORT))
    
# plt.pcolormesh(times, frequencies, 10*np.log10(spectrogram))
# plt.show()

spectrogram = 5*np.log10(spectrogram)

for i in range(129):
    spectrogram[i] /= spectrogram[i].max()
    spectrogram[i] *= 255

spectrogram[spectrogram < 0] = 0

# print(spectrogram[0].max())
# plt.plot(spectrogram[0])
# plt.show()

prev_time = 0

for i, t in enumerate(times):
    spec = [int(spectrogram[x][i]) for x in range(129)]
    spec = np.interp(np.linspace(0, len(spec) - 1, num=288), np.arange(len(spec)), spec)
    data = {
        "leds": list(range(288)),
        "values": [(x, x, x) for x in spec]
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(pickle.dumps(data), (UDP_IP, UDP_PORT))

    # print(sys.getsizeof(pickle.dumps(data)))

    time.sleep(t - prev_time)
    prev_time = t

# data = {
#     "leds": [0, 25, 200],
#     "values": [(255, 0, 0), (0, 255, 255), (255, 255, 0)]
# }

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.sendto(pickle.dumps(data), (UDP_IP, UDP_PORT))