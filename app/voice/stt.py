import azure.cognitiveservices.speech as speechsdk
from app.config import settings


class STTService:
    def __init__(self):
        if not settings.azure_speech_key or not settings.azure_speech_region:
            raise ValueError("Azure Speech settings are missing")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        self.speech_config.speech_recognition_language = "en-US"

    def transcribe_pcm_bytes(self, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=sample_rate,
            bits_per_sample=16,
            channels=1,
        )

        stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
        stream.write(pcm_bytes)
        stream.close()

        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return (result.text or "").strip()

        return ""