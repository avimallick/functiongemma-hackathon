"""
Kagami API — FastAPI backend for hybrid edge-cloud tool calling.
"""

import os
import time
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from google import genai
from google.genai import types
from main import generate_hybrid, generate_cactus, generate_cloud

app = FastAPI(title="Kagami API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ==================== Tool Definitions ====================

AVAILABLE_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City name"}},
            "required": ["location"],
        },
    },
    {
        "name": "set_alarm",
        "description": "Set an alarm for a given time",
        "parameters": {
            "type": "object",
            "properties": {
                "hour": {"type": "integer", "description": "Hour (0-23)"},
                "minute": {"type": "integer", "description": "Minute (0-59)"},
            },
            "required": ["hour", "minute"],
        },
    },
    {
        "name": "send_message",
        "description": "Send a message to a contact",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Name of the person"},
                "message": {"type": "string", "description": "Message content"},
            },
            "required": ["recipient", "message"],
        },
    },
    {
        "name": "create_reminder",
        "description": "Create a reminder with a title and time",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Reminder title"},
                "time": {"type": "string", "description": "Time (e.g. 3:00 PM)"},
            },
            "required": ["title", "time"],
        },
    },
    {
        "name": "search_contacts",
        "description": "Search for a contact by name",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Name to search for"}},
            "required": ["query"],
        },
    },
    {
        "name": "play_music",
        "description": "Play a song or playlist",
        "parameters": {
            "type": "object",
            "properties": {"song": {"type": "string", "description": "Song or playlist name"}},
            "required": ["song"],
        },
    },
    {
        "name": "set_timer",
        "description": "Set a countdown timer",
        "parameters": {
            "type": "object",
            "properties": {"minutes": {"type": "integer", "description": "Number of minutes"}},
            "required": ["minutes"],
        },
    },
]


# ==================== Gemini Chat Client ====================

def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


def gemini_chat(message: str) -> str:
    """Use Gemini as a general chat assistant (no tools)."""
    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[message],
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are Kagami, a helpful and concise personal assistant. "
                "Answer the user's question directly. Keep responses brief — "
                "2-3 sentences max unless the question requires more detail."
            ),
            temperature=0.3,
        ),
    )
    return response.text.strip() if response.text else "I'm not sure about that."


# ==================== Validation ====================

def validate_calls(calls, user_message):
    """Filter out invalid, empty, or hallucinated tool calls."""
    lower = user_message.lower().strip()
    clean = []

    for c in calls:
        name = c.get("name", "")
        args = c.get("arguments", {})

        # Skip calls with empty string args
        if any(isinstance(v, str) and not v.strip() for v in args.values()):
            continue

        # Validate argument ranges
        if name == "set_alarm":
            h, m = args.get("hour"), args.get("minute")
            if not (isinstance(h, int) and isinstance(m, int) and 0 <= h <= 23 and 0 <= m <= 59):
                continue
        if name == "set_timer":
            mins = args.get("minutes")
            if not (isinstance(mins, int) and 0 < mins <= 1440):
                continue

        # Detect hallucinated send_message (model echoes the question as a message)
        if name == "send_message":
            msg_arg = args.get("message", "").lower()
            if msg_arg and (msg_arg in lower or lower in msg_arg):
                continue

        # Detect hallucinated create_note (model echoes the question as content)
        if name == "create_note":
            content = args.get("content", "").lower()
            if content and (content in lower or lower in content):
                continue

        clean.append(c)

    # Detect unsupported requests (seconds-based timers/alarms)
    if any(w in lower for w in ["seconds", "second"]):
        clean = [c for c in clean if c.get("name") not in ("set_alarm", "set_timer")]

    return clean


def is_tool_action(message: str) -> bool:
    """Quick check: does this message look like it wants a tool action?"""
    lower = message.lower().strip()
    action_signals = [
        "set alarm", "set timer", "set a timer", "alarm for", "alarm at",
        "play ", "remind me", "send message", "send a message",
        "text ", "message ", "wake me", "timer for",
        "note", "calendar", "schedule", "translate",
        "weather", "temperature", "forecast",
        "find ", "look up", "search ",
    ]
    return any(kw in lower for kw in action_signals)


# ==================== Models ====================

class ChatRequest(BaseModel):
    message: str
    tools: Optional[list] = None


class ToolCall(BaseModel):
    name: str
    arguments: dict


class ChatResponse(BaseModel):
    function_calls: list[ToolCall]
    source: str
    confidence: float
    total_time_ms: float
    message: str


# ==================== Endpoints ====================

@app.get("/")
def health():
    return {
        "status": "ok",
        "engine": "FunctionGemma 270M + Gemini 2.0 Flash (Hybrid)",
        "tools_available": len(AVAILABLE_TOOLS),
    }


@app.get("/tools")
def list_tools():
    return {"tools": AVAILABLE_TOOLS}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    tools = req.tools or AVAILABLE_TOOLS
    messages = [{"role": "user", "content": req.message}]
    start = time.time()

    # If it doesn't look like a tool action at all, go straight to chat
    if not is_tool_action(req.message):
        try:
            answer = gemini_chat(req.message)
            elapsed = (time.time() - start) * 1000
            return ChatResponse(
                function_calls=[], source="cloud (chat)",
                confidence=1.0, total_time_ms=elapsed, message=answer,
            )
        except Exception as e:
            traceback.print_exc()
            return ChatResponse(
                function_calls=[], source="error",
                confidence=0.0, total_time_ms=0,
                message=f"Sorry, couldn't process that. ({type(e).__name__})",
            )

    # Looks like a tool action — try hybrid routing
    try:
        result = generate_hybrid(messages, tools)
    except Exception as e:
        traceback.print_exc()
        result = {"function_calls": []}

    calls = validate_calls(result.get("function_calls", []), req.message)
    source = result.get("source", "unknown")
    confidence = float(result.get("confidence", 0.0) or 0.0)
    total_time_ms = float(result.get("total_time_ms", 0.0))

    # If valid tool calls, return them
    if calls:
        if len(calls) == 1:
            summary = f"Done! I've executed: {calls[0]['name'].replace('_', ' ')}"
        else:
            names = [c["name"].replace("_", " ") for c in calls]
            summary = f"Got it! I've handled {len(calls)} actions: {', '.join(names)}"

        return ChatResponse(
            function_calls=[ToolCall(name=c["name"], arguments=c.get("arguments", {})) for c in calls],
            source=source, confidence=confidence,
            total_time_ms=total_time_ms, message=summary,
        )

    # Tool routing returned nothing valid — fall back to chat
    try:
        answer = gemini_chat(req.message)
        elapsed = (time.time() - start) * 1000
        return ChatResponse(
            function_calls=[], source="cloud (chat)",
            confidence=1.0, total_time_ms=elapsed, message=answer,
        )
    except Exception as e:
        traceback.print_exc()
        return ChatResponse(
            function_calls=[], source="error",
            confidence=0.0, total_time_ms=total_time_ms,
            message=f"Sorry, couldn't process that. ({type(e).__name__})",
        )


@app.post("/chat/local")
def chat_local(req: ChatRequest):
    tools = req.tools or AVAILABLE_TOOLS
    messages = [{"role": "user", "content": req.message}]
    result = generate_cactus(messages, tools)
    return {
        "function_calls": result.get("function_calls", []),
        "confidence": float(result.get("confidence", 0.0) or 0.0),
        "total_time_ms": float(result.get("total_time_ms", 0.0)),
        "source": "on-device",
    }


@app.post("/chat/cloud")
def chat_cloud(req: ChatRequest):
    tools = req.tools or AVAILABLE_TOOLS
    messages = [{"role": "user", "content": req.message}]
    result = generate_cloud(messages, tools)
    return {
        "function_calls": result.get("function_calls", []),
        "total_time_ms": float(result.get("total_time_ms", 0.0)),
        "source": "cloud",
    }


@app.post("/compare")
def compare(req: ChatRequest):
    """Run all three engines side-by-side."""
    tools = req.tools or AVAILABLE_TOOLS
    messages = [{"role": "user", "content": req.message}]

    # Local — always fast, never fails
    try:
        local = generate_cactus(messages, tools)
    except Exception:
        local = {"function_calls": [], "confidence": 0.0, "total_time_ms": 0.0}

    # Cloud — can timeout or fail
    try:
        cloud = generate_cloud(messages, tools)
    except Exception as e:
        traceback.print_exc()
        cloud = {"function_calls": [], "total_time_ms": 0.0}

    # Hybrid — our routing engine
    try:
        hybrid = generate_hybrid(messages, tools)
    except Exception as e:
        traceback.print_exc()
        hybrid = {"function_calls": [], "source": "error", "confidence": 0.0, "total_time_ms": 0.0}

    return {
        "message": req.message,
        "local": {
            "function_calls": local.get("function_calls", []),
            "confidence": float(local.get("confidence", 0.0) or 0.0),
            "total_time_ms": float(local.get("total_time_ms", 0.0)),
        },
        "cloud": {
            "function_calls": cloud.get("function_calls", []),
            "total_time_ms": float(cloud.get("total_time_ms", 0.0)),
        },
        "hybrid": {
            "function_calls": hybrid.get("function_calls", []),
            "source": hybrid.get("source", "unknown"),
            "confidence": float(hybrid.get("confidence", 0.0) or 0.0),
            "total_time_ms": float(hybrid.get("total_time_ms", 0.0)),
        },
    }
