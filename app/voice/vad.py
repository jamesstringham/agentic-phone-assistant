from collections import deque
import torch
import numpy as np


class SileroVADState:
    def __init__(
        self,
        sample_rate=8000,
        threshold=0.45,
        min_speech_ms=160,
        end_silence_ms=600,
        chunk_ms=32,
        preroll_ms=256,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.chunk_ms = chunk_ms

        # bytes, not samples
        self.bytes_per_chunk = int(sample_rate * chunk_ms / 1000) * 2  # 16-bit mono PCM

        self.min_speech_chunks = max(1, min_speech_ms // chunk_ms)
        self.end_silence_chunks = max(1, end_silence_ms // chunk_ms)
        self.preroll_chunks = max(1, preroll_ms // chunk_ms)

        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )

        self.reset()

    def reset(self):
        self.buffer = []
        self.preroll = deque(maxlen=self.preroll_chunks)
        self.triggered = False
        self.speech_count = 0
        self.silence_count = 0

    def process_chunk(self, pcm_chunk: bytes):
        """
        pcm_chunk: 16-bit PCM mono @ 8kHz
        returns:
            dict | None

        Result dict:
        {
            "event": "speech_start" | "speech_end",
            "audio": bytes | None,
        }
        """
        self.preroll.append(pcm_chunk)

        audio = torch.from_numpy(
            np.frombuffer(pcm_chunk, dtype=np.int16)
        ).float() / 32768.0

        speech_prob = self.model(audio, self.sample_rate).item()

        if not self.triggered:
            if speech_prob > self.threshold:
                self.speech_count += 1
            else:
                self.speech_count = 0

            if self.speech_count >= self.min_speech_chunks:
                self.triggered = True
                self.buffer.extend(self.preroll)
                self.silence_count = 0
                return {"event": "speech_start", "audio": None}

            return None

        self.buffer.append(pcm_chunk)

        if speech_prob < self.threshold:
            self.silence_count += 1
        else:
            self.silence_count = 0

        if self.silence_count >= self.end_silence_chunks:
            utterance = b"".join(self.buffer)
            self.reset()
            return {"event": "speech_end", "audio": utterance}

        return None