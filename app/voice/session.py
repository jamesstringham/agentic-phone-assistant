from dataclasses import dataclass, field

@dataclass
class CallSession:
    call_connection_id: str
    correlation_id: str
    sample_rate: int = 16000
    channels: int = 1
    audio_encoding: str = "PCM"
    inbound_buffer: bytearray = field(default_factory=bytearray)
    silence_frames: int = 0