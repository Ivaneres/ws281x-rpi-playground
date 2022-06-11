import spotipy
from spotipy.oauth2 import SpotifyOAuth
from threading import Timer


class SpotifyPlayingMonitor:
    
    def __init__(self, interval=5) -> None:
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-currently-playing"))
        self.playing = None
        self.__timer = None
        self.interval = interval
        self.start()
        
    def __func(self):
        self.playing = self.sp.current_user_playing_track()
        print("Sending a spotify api request")
        
    def __run(self):
        self.start()
        self.__func()
        
    def start(self):
        self.__func()
        self.__timer = Timer(self.interval, self.__run)
        self.__timer.start()
