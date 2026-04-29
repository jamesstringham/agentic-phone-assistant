import asyncio
import html
import threading
import azure.cognitiveservices.speech as speechsdk
from app.config import settings


class TTSService:
    def __init__(self):
        if not settings.azure_speech_key or not settings.azure_speech_region:
            raise ValueError("Azure Speech settings are missing")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )

        self.voice_name = settings.azure_speech_voice or "en-US-Aria:DragonHDLatestNeural"

        self.telephony_native = True
        try:
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw
            )
        except Exception:
            self.telephony_native = False
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
            )

        # Reuse a single synthesizer instance
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None,
        )

        # Azure SDK objects are not something I’d assume are safe for parallel writes,
        # so serialize synthesis through a lock.
        self._lock = threading.Lock()

        # Filled during warmup
        self.cached_welcome_audio: tuple[bytes, str] | None = None

    def build_ssml_for_text(self, text: str) -> str:
        escaped_text = html.escape(text)
        return f"""
<speak xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts"
       version="1.0"
       xml:lang="en-US">
  <voice name="{self.voice_name}">
    <mstts:express-as style="friendly" styledegree="1.0">
      <prosody rate="-4%" pitch="0%">
        {escaped_text}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>
""".strip()

    def synthesize_ssml_bytes(self, ssml: str) -> tuple[bytes, str]:
        with self._lock:
            result = self.synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio = bytes(result.audio_data)
            if self.telephony_native:
                return audio, "mulaw_8k_raw"
            return audio, "wav_24k"

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_details = getattr(cancellation, "error_details", None)
            raise RuntimeError(
                f"TTS synthesis canceled. "
                f"reason={cancellation.reason}, "
                f"error_details={error_details}"
            )

        raise RuntimeError(f"TTS synthesis failed: {result.reason}")

    def synthesize_text_bytes(self, text: str) -> tuple[bytes, str]:
        ssml = self.build_ssml_for_text(text)
        return self.synthesize_ssml_bytes(ssml)

    async def warm_up(self, welcome_ssml: str) -> None:
        loop = asyncio.get_running_loop()

        # Tiny warmup request to reduce first real synthesis latency
        await loop.run_in_executor(None, self.synthesize_text_bytes, "Hello.")

        # Cache welcome greeting
        self.cached_welcome_audio = await loop.run_in_executor(
            None,
            self.synthesize_ssml_bytes,
            welcome_ssml,
        )