import os
import tempfile

import pyttsx3
from gtts import gTTS
from playsound import playsound


class Speaker:
    def __init__(self) -> None:
        self.engine_name = os.getenv("TTS_ENGINE", "gtts").lower()
        self._pyttsx3 = None
        if self.engine_name == "pyttsx3":
            self._pyttsx3 = pyttsx3.init()
            self._pyttsx3.setProperty("rate", 175)

    def say(self, text: str) -> None:
        print(f"Jarvis: {text}")
        if self.engine_name == "pyttsx3":
            self._say_pyttsx3(text)
        else:
            self._say_gtts(text)

    def _say_gtts(self, text: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_audio:
            gTTS(text=text, lang="ko").save(temp_audio.name)
            playsound(temp_audio.name)

    def _say_pyttsx3(self, text: str) -> None:
        if self._pyttsx3 is None:
            self._pyttsx3 = pyttsx3.init()
        self._pyttsx3.say(text)
        self._pyttsx3.runAndWait()
