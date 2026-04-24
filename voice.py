from __future__ import annotations

import os
import tempfile

import numpy as np
import sounddevice as sd
import speech_recognition as sr
import whisper


class VoiceInput:
    def __init__(self, wake_word: str = "자비스") -> None:
        self.wake_word = wake_word
        self.engine = os.getenv("VOICE_INPUT_ENGINE", "speech_recognition").lower()
        self.recognizer = sr.Recognizer()
        self._whisper_model = None

    def listen_once(self, timeout: int | None = 5, phrase_time_limit: int | None = 8) -> str:
        if self.engine == "whisper":
            return self._listen_with_whisper(seconds=phrase_time_limit or 8)
        return self._listen_with_speech_recognition(timeout, phrase_time_limit)

    def wait_for_wake_word(self) -> None:
        print(f'Wake word 대기 중: "{self.wake_word}"')
        while True:
            text = self.listen_once(timeout=None, phrase_time_limit=4)
            if not text:
                continue
            print(f"사용자: {text}")
            if self.wake_word in text.replace(" ", ""):
                return

    def listen_command(self) -> str:
        print("명령을 말씀하세요.")
        return self.listen_once(timeout=8, phrase_time_limit=12)

    def _listen_with_speech_recognition(
        self,
        timeout: int | None,
        phrase_time_limit: int | None,
    ) -> str:
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return ""

        try:
            return self.recognizer.recognize_google(audio, language="ko-KR").strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            print(f"음성 인식 API 오류: {exc}")
            return ""

    def _listen_with_whisper(self, seconds: int = 8) -> str:
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model("base")

        sample_rate = 16_000
        print(f"{seconds}초 동안 녹음합니다.")
        audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()

        audio = np.squeeze(audio).astype(np.float32)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
            import wave

            pcm = np.clip(audio, -1.0, 1.0)
            pcm = (pcm * 32767).astype(np.int16)
            with wave.open(temp_audio.name, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm.tobytes())

            result = self._whisper_model.transcribe(temp_audio.name, language="ko")
            return str(result.get("text", "")).strip()
