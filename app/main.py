from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect

from app.config import settings
from app.agents.conversation_agent import ConversationAgent
from app.voice.stt import STTService
from app.voice.tts import TTSService
from app.voice.twilio_media import handle_twilio_media_socket
from app.prompts.welcome_ssml import WELCOME_SSML
from app.graph.graph import build_graph

app = FastAPI()


@app.on_event("startup")
async def startup():
    app.state.conversation_agent = ConversationAgent()
    app.state.stt_service = STTService()
    app.state.tts_service = TTSService()
    app.state.call_graph = build_graph()

    await app.state.tts_service.warm_up(WELCOME_SSML)

    print("[STARTUP] services initialized and TTS warmed")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/voice")
async def voice_webhook(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    from_number = form.get("From")
    to_number = form.get("To")

    print(f"[TWILIO INCOMING CALL] call_sid={call_sid} from={from_number} to={to_number}")

    ws_url = settings.media_ws_url

    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)

    return Response(content=str(response), media_type="application/xml")


@app.post("/twilio/status")
async def twilio_status(request: Request):
    form = await request.form()
    print("[TWILIO STATUS]", dict(form))
    return JSONResponse({"status": "ok"})


@app.websocket("/ws/media")
async def media_ws(websocket: WebSocket):
    await handle_twilio_media_socket(
        websocket=websocket,
        conversation_agent=app.state.conversation_agent,
        stt_service=app.state.stt_service,
        tts_service=app.state.tts_service,
        call_graph=app.state.call_graph,
    )