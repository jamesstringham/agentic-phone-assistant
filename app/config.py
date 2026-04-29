import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")

    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    azure_speech_key: str = os.getenv("AZURE_SPEECH_KEY", "")
    azure_speech_region: str = os.getenv("AZURE_SPEECH_REGION", "")
    azure_speech_voice: str = os.getenv("AZURE_SPEECH_VOICE", "en-US-JennyNeural")

    @property
    def voice_webhook_url(self) -> str:
        return f"{self.public_base_url}/voice"

    @property
    def media_ws_url(self) -> str:
        base = self.public_base_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/ws/media"


settings = Settings()