# AI Phone Assistant (Voice Agent)

This project is a real-time AI phone assistant that handles live phone calls, understands user intent, and responds conversationally using speech.

It integrates telephony, speech processing, and LLM-based decision making into a single system capable of managing tasks like appointment scheduling and general inquiries.

This project is currently under active development, with ongoing work focused on retrieval-augmented generation (RAG) and expanded multi-agent capabilities.

---

## Overview

The system connects a live phone call to an AI agent pipeline:

1. Incoming call is handled via Twilio
2. Audio is streamed to a FastAPI WebSocket server
3. Speech is transcribed using Azure Speech-to-Text
4. A LangGraph-based agent system processes the request
5. The assistant generates a response using Azure OpenAI
6. The response is converted to speech using Azure Text-to-Speech
7. Audio is streamed back to the caller in real time

---

## Key Features

- Real-time phone call handling with Twilio Media Streams
- Streaming audio pipeline (8kHz μ-law → PCM → transcription)
- Voice Activity Detection (Silero VAD) for turn detection
- Barge-in support (caller can interrupt assistant speech)
- Azure Speech integration for STT and TTS
- Azure OpenAI integration with tool-calling support
- LangGraph-based multi-agent routing system
- Modular specialist agents (scheduling, business info, etc.)
- Structured tool execution for real-world actions

---

## Architecture

### Backend (FastAPI)
- Handles Twilio webhooks (`/voice`)
- Manages WebSocket media stream (`/ws/media`)
- Coordinates STT, agent execution, and TTS

### Voice Pipeline
- Incoming μ-law audio → PCM conversion
- Chunked processing + VAD for speech segmentation
- Transcription via Azure Speech
- Response synthesized and streamed back in real time

### Agent System

The agent system is built using a graph-based architecture:

- Router Agent: Determines intent and routes requests
- Specialist Agents: Handle specific tasks like scheduling
- State Management: Maintains conversation context
- LangGraph Workflow: Controls routing and execution

---

## Project Structure

app/
├── agents/
├── graph/
├── llm/
├── prompts/
├── rag/
├── tools/
├── voice/
├── config.py
└── main.py

---

## Technologies Used

- Python, FastAPI
- Twilio (Voice + Media Streams)
- Azure OpenAI
- Azure Speech (STT + TTS)
- LangGraph
- PyTorch (Silero VAD)
- WebSockets

---

## Running the Project

1. Install dependencies  
pip install -r requirements.txt

2. Configure environment variables using `.env.example`

3. Start the server  
uvicorn app.main:app --reload

4. Connect Twilio webhook to `/voice` and media stream to `/ws/media`

---

## Current Status

Functional prototype supporting:
- Real-time call handling
- Speech transcription and synthesis
- Agent routing and responses
- Tool-based scheduling (demo)

---

## In Progress

- Retrieval-Augmented Generation (RAG)
- Additional specialist agents
- Persistent memory
- Performance improvements

---

## Author

James Stringham
