from audioop import rms
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

UDP_IP = "192.168.1.126"
UDP_PORT = 5005

 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = int(44100 / 20)

p = pyaudio.PyAudio()
 
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

colour_gradient = (np.array([29, 255, 113]), np.array([189, 72, 232]))

def encode_tuple(tup):
    return "|".join(map(str, tup)).encode()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto("wave".encode(), (UDP_IP, UDP_PORT))

while True:
    data = stream.read(CHUNK)
    data = np.frombuffer(data, dtype=np.int16)

    fourier = np.abs(np.fft.rfft(data))
    # p = np.where(fourier > 0, np.log(fourier), 0)
    p = fourier
    freqs = np.fft.rfftfreq(data.size, d=1./RATE)

    bass = np.sum(p[freqs < 150])
    mids = np.sum(p[(freqs > 150) & (freqs < 4000)])
    treble = np.sum(p[freqs > 4000])
    
    bass_ratio = 1.5 * bass / np.sum(p)
    if bass_ratio > 1:
        bass_ratio = 1.0

    colour = np.nan_to_num((colour_gradient[0] * bass_ratio + colour_gradient[1] * (1 - bass_ratio)))

    # frequencies = []

    # for l, r in zip(frequency_bins, frequency_bins[1:]):
    #     frequencies.append(p[(freqs < r) & (freqs > l)].mean())

    # f_min, f_max = np.min(frequencies), np.max(frequencies)

    # if f_max - f_min > 0:
    #     frequencies = ((frequencies - f_min) / (f_max - f_min)) * 255
    # frequencies = np.array(frequencies).astype(int)

    # print(frequencies)
    # plt.plot(freqs, p)
    # plt.show()

    # f, t, spectrogram = signal.spectrogram(data)

    # # spectrogram = np.log10(spectrogram)

    # for i in range(129):
    #     spectrogram[i] /= spectrogram[i].max()
    #     spectrogram[i] *= 255

    # spectrogram[spectrogram < 0] = 0
    # spectrogram[np.isnan(spectrogram)] = 0

    # spec = [spectrogram[x][0] for x in range(129)]
    # spec = np.interp(np.linspace(0, len(spec) - 1, num=288), np.arange(len(spec)), spec)
    # spec = spec.astype(int)
    # print(max(spec), min(spec))

    # print(np.min(frequencies), np.max(frequencies))
    
    rms_amp = (np.sqrt(np.mean((data * 1./32768) ** 2)) / 0.6).item()
    if rms_amp > 1.0:
        rms_amp = 1.0
    # log_rms = 20 * np.log10(rms_amp)
    rms_amp = rms_amp
    # print(rms_amp, type(rms_amp))

    scaled_colour = rms_amp * colour
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