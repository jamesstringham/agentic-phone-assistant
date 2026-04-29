import audioop
import base64
import json
import uuid
import re
from io import BytesIO
import wave
from fastapi import WebSocket, WebSocketDisconnect
from app.prompts.welcome_ssml import WELCOME_SSML
from app.voice.vad import SileroVADState

call_states = {}

def mulaw_to_pcm16(mulaw_bytes: bytes) -> bytes:
    return audioop.ulaw2lin(mulaw_bytes, 2)


def pcm16_to_mulaw(pcm_bytes: bytes) -> bytes:
    return audioop.lin2ulaw(pcm_bytes, 2)


def downsample_24k_to_8k(pcm_bytes: bytes) -> bytes:
    converted, _ = audioop.ratecv(pcm_bytes, 2, 1, 24000, 8000, None)
    return converted


def upsample_8k_to_16k(pcm_bytes: bytes) -> bytes:
    converted, _ = audioop.ratecv(pcm_bytes, 2, 1, 8000, 16000, None)
    return converted


def wav_bytes_to_pcm16(wav_bytes: bytes) -> bytes:
    with wave.open(BytesIO(wav_bytes), "rb") as wf:
        return wf.readframes(wf.getnframes())


def chunk_bytes(data: bytes, size: int):
    for i in range(0, len(data), size):
        yield data[i:i + size]


async def send_mark(websocket: WebSocket, stream_sid: str, name: str) -> None:
    msg = {
        "event": "mark",
        "streamSid": stream_sid,
        "mark": {"name": name},
    }
    await websocket.send_text(json.dumps(msg))


async def send_clear(websocket: WebSocket, stream_sid: str) -> None:
    msg = {
        "event": "clear",
        "streamSid": stream_sid,
    }
    await websocket.send_text(json.dumps(msg))

async def send_precomputed_tts_audio_to_twilio(
    websocket: WebSocket,
    stream_sid: str,
    audio_bytes: bytes,
    audio_kind: str,
) -> str:
    if audio_kind == "mulaw_8k_raw":
        mulaw_audio = audio_bytes
    elif audio_kind == "wav_24k":
        reply_pcm_24k = wav_bytes_to_pcm16(audio_bytes)
        reply_pcm_8k = downsample_24k_to_8k(reply_pcm_24k)
        mulaw_audio = pcm16_to_mulaw(reply_pcm_8k)
    else:
        raise RuntimeError(f"Unsupported TTS audio_kind: {audio_kind}")

    mark_name = f"assistant_done:{uuid.uuid4().hex}"
    await send_mulaw_to_twilio(websocket, stream_sid, mulaw_audio, mark_name=mark_name)
    return mark_name

async def send_tts_ssml_to_twilio(
    websocket: WebSocket,
    stream_sid: str,
    tts_service,
    ssml: str,
) -> str:
    audio_bytes, audio_kind = tts_service.synthesize_ssml_bytes_with_kind(ssml)

    if audio_kind == "mulaw_8k_raw":
        mulaw_audio = audio_bytes
    elif audio_kind == "wav_24k":
        reply_pcm_24k = wav_bytes_to_pcm16(audio_bytes)
        reply_pcm_8k = downsample_24k_to_8k(reply_pcm_24k)
        mulaw_audio = pcm16_to_mulaw(reply_pcm_8k)
    else:
        raise RuntimeError(f"Unsupported TTS audio_kind: {audio_kind}")

    mark_name = f"assistant_done:{uuid.uuid4().hex}"
    await send_mulaw_to_twilio(websocket, stream_sid, mulaw_audio, mark_name=mark_name)
    return mark_name


async def send_mulaw_to_twilio(
    websocket: WebSocket,
    stream_sid: str,
    mulaw_bytes: bytes,
    mark_name: str | None = None,
) -> None:
    # 160 bytes = 20ms of 8kHz 8-bit mu-law mono
    for chunk in chunk_bytes(mulaw_bytes, 160):
        outbound = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": base64.b64encode(chunk).decode("utf-8")
            }
        }
        await websocket.send_text(json.dumps(outbound))

    if mark_name:
        await send_mark(websocket, stream_sid, mark_name)


async def send_tts_audio_to_twilio(
    websocket: WebSocket,
    stream_sid: str,
    tts_service,
    text: str,
) -> str:
    """
    Sends assistant speech and returns the playback mark name.
    """
    audio_bytes, audio_kind = tts_service.synthesize_text_bytes(text)

    if audio_kind == "mulaw_8k_raw":
        mulaw_audio = audio_bytes
    elif audio_kind == "wav_24k":
        reply_pcm_24k = wav_bytes_to_pcm16(audio_bytes)
        reply_pcm_8k = downsample_24k_to_8k(reply_pcm_24k)
        mulaw_audio = pcm16_to_mulaw(reply_pcm_8k)
    else:
        raise RuntimeError(f"Unsupported TTS audio_kind: {audio_kind}")

    mark_name = f"assistant_done:{uuid.uuid4().hex}"
    await send_mulaw_to_twilio(websocket, stream_sid, mulaw_audio, mark_name=mark_name)
    return mark_name


class SentenceChunker:
    def __init__(self, min_chunk_chars: int = 70, max_chunk_chars: int = 220):
        self.buffer = ""
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars

        # Common abbreviations that should not end a sentence
        self.abbreviations = {
            "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.",
            "st.", "vs.", "etc.", "e.g.", "i.e.",
            "a.m.", "p.m."
        }

    def push(self, text: str) -> list[str]:
        self.buffer += text
        self.buffer = re.sub(r"\s+", " ", self.buffer)

        ready = []

        while True:
            split_idx = self._find_best_split(self.buffer)
            if split_idx is None:
                break

            candidate = self.buffer[:split_idx].strip()
            remaining = self.buffer[split_idx:].lstrip()

            if not candidate:
                self.buffer = remaining
                continue

            # Avoid speaking tiny awkward chunks unless buffer is getting large
            if len(candidate) < self.min_chunk_chars and len(self.buffer) < self.max_chunk_chars:
                break

            ready.append(candidate)
            self.buffer = remaining

        # Safety valve: if buffer gets too large, split at a softer boundary
        if len(self.buffer) >= self.max_chunk_chars:
            split_idx = self._find_soft_split(self.buffer)
            if split_idx is not None:
                candidate = self.buffer[:split_idx].strip()
                self.buffer = self.buffer[split_idx:].lstrip()
                if candidate:
                    ready.append(candidate)

        return ready

    def flush(self) -> str:
        remaining = self.buffer.strip()
        self.buffer = ""
        return remaining

    def _find_best_split(self, text: str) -> int | None:
        """
        Return index AFTER the split point.
        Looks for real sentence endings, but skips common abbreviations.
        """
        for match in re.finditer(r'[.!?](?=\s+|$)', text):
            end_idx = match.end()
            prefix = text[:end_idx].strip()
            last_word = prefix.split()[-1].lower() if prefix.split() else ""

            if last_word in self.abbreviations:
                continue

            return end_idx

        return None

    def _find_soft_split(self, text: str) -> int | None:
        """
        If no sentence boundary is good enough and the buffer is getting long,
        split on the last comma or space near the max length.
        """
        window = text[:self.max_chunk_chars]

        comma_idx = window.rfind(",")
        if comma_idx >= self.min_chunk_chars:
            return comma_idx + 1

        space_idx = window.rfind(" ")
        if space_idx >= self.min_chunk_chars:
            return space_idx + 1

        return None

    def flush(self) -> str:
        remaining = self.buffer.strip()
        self.buffer = ""
        return remaining

async def handle_twilio_media_socket(
    websocket: WebSocket,
    conversation_agent,
    stt_service,
    tts_service,
    call_graph,
):
    await websocket.accept()

    stream_sid = None
    call_sid = None
    pcm_buffer = bytearray()

    # True while Twilio is still expected to be PLAYING assistant audio
    assistant_playing = False
    active_playback_marks = set()

    vad_state = SileroVADState(
        sample_rate=8000,
        threshold=0.45,
        min_speech_ms=160,
        end_silence_ms=800,
        chunk_ms=32,
        preroll_ms=256,
    )

    print("[WS CONNECTED] Twilio media socket connected")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            event = msg.get("event")

            if event == "connected":
                print("[TWILIO WS] connected")

            elif event == "start":
                stream_sid = msg["start"]["streamSid"]
                call_sid = msg["start"]["callSid"]
                media_format = msg["start"].get("mediaFormat", {})
                print(f"[TWILIO WS] start stream_sid={stream_sid} call_sid={call_sid} media_format={media_format}")

                if tts_service.cached_welcome_audio is None:
                    raise RuntimeError("TTS welcome audio was not warmed/cached at startup")

                welcome_audio, welcome_kind = tts_service.cached_welcome_audio
                mark_name = await send_precomputed_tts_audio_to_twilio(
                    websocket=websocket,
                    stream_sid=stream_sid,
                    audio_bytes=welcome_audio,
                    audio_kind=welcome_kind,
                )
                assistant_playing = True
                active_playback_marks.add(mark_name)

            elif event == "mark":
                mark = msg.get("mark", {})
                mark_name = mark.get("name")
                print(f"[TWILIO WS] mark received name={mark_name}")

                if mark_name in active_playback_marks:
                    active_playback_marks.remove(mark_name)

                if not active_playback_marks:
                    assistant_playing = False

            elif event == "media":
                payload_b64 = msg["media"]["payload"]
                mulaw_chunk = base64.b64decode(payload_b64)
                pcm_8k = mulaw_to_pcm16(mulaw_chunk)
                pcm_buffer.extend(pcm_8k)

                frame_size = vad_state.bytes_per_chunk

                while len(pcm_buffer) >= frame_size:
                    frame = bytes(pcm_buffer[:frame_size])
                    del pcm_buffer[:frame_size]

                    vad_result = vad_state.process_chunk(frame)
                    if vad_result is None:
                        continue

                    if vad_result["event"] == "speech_start":
                        # Caller started speaking while bot audio may still be buffered/playing.
                        # Clear Twilio’s outbound audio buffer to support barge-in.
                        if assistant_playing and stream_sid:
                            print("[BARGE-IN] caller speech detected; clearing assistant audio")
                            await send_clear(websocket, stream_sid)
                            assistant_playing = False
                            active_playback_marks.clear()

                        continue

                    if vad_result["event"] == "speech_end":
                        utterance_pcm_8k = vad_result["audio"]
                        if not utterance_pcm_8k:
                            continue

                        print(f"[VAD] finalized utterance bytes={len(utterance_pcm_8k)}")

                        utterance_pcm_16k = upsample_8k_to_16k(utterance_pcm_8k)
                        user_text = stt_service.transcribe_pcm_bytes(
                            utterance_pcm_16k,
                            sample_rate=16000,
                        )
                        print(f"[USER TEXT] {user_text}")

                        if not user_text.strip():
                            continue

                        session_id = call_sid or "twilio-call"

                        # 1. Load existing state (or create new)
                        state = call_states.get(session_id, {
                            "session_id": session_id,
                            "caller_phone": session_id,
                        })

                        # 2. Update with new user message
                        state["user_message"] = user_text

                        # 3. Run graph
                        new_state = call_graph.invoke(state)

                        # 4. Save updated state
                        call_states[session_id] = new_state

                        assistant_text = new_state.get("assistant_message", "")

                        print(f"[ASSISTANT TEXT FULL] {assistant_text}")

                        if not assistant_text:
                            continue

                        chunker = SentenceChunker(min_chunk_chars=90, max_chunk_chars=240)

                        ready_sentences = chunker.push(assistant_text)
                        for sentence in ready_sentences:
                            print(f"[ASSISTANT TEXT CHUNK] {sentence}")
                            mark_name = await send_tts_audio_to_twilio(
                                websocket=websocket,
                                stream_sid=stream_sid,
                                tts_service=tts_service,
                                text=sentence,
                            )
                            assistant_playing = True
                            active_playback_marks.add(mark_name)

                        remaining = chunker.flush()
                        if remaining:
                            print(f"[ASSISTANT TEXT CHUNK] {remaining}")
                            mark_name = await send_tts_audio_to_twilio(
                                websocket=websocket,
                                stream_sid=stream_sid,
                                tts_service=tts_service,
                                text=remaining,
                            )
                            assistant_playing = True
                            active_playback_marks.add(mark_name)

            elif event == "stop":
                print(f"[TWILIO WS] stop call_sid={call_sid} stream_sid={stream_sid}")
                if call_sid in call_states:
                    del call_states[call_sid]
                break

    except WebSocketDisconnect:
        print("[WS DISCONNECTED] Twilio media socket disconnected")