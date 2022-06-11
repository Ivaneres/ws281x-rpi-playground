# ws281x-rpi-playground

A collection of short scripts written to drive a strip of ws281x LEDs from a Raspberry Pi.

Currently includes:
 - Music visualisation with Spotify album art integration
 - An outline for CS:GO game state integration

## Installation
To run the music visualiser, set `UDP_IP` in `rpi_led_client.py` to the IP of the RPi. A loopback device is necesary on the client machine to monitor system audio (note, this only works nicely on Linux). Run the `rpi_led_client.py` script to get a list of devices and their indexes, and set the `input_device_index` to the loopback device in the script. Execute `led_udp.py` on the RPi and `rpi_led_client.py` on the client machine.

For Spotify integration, create a file `spotify.env` in the root dir of the project containing Spotify app details `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`, which can be created [here](https://developer.spotify.com/dashboard/applications).
