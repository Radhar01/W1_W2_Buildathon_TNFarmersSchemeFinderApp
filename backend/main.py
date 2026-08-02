"""
main.py  -  The FastAPI backend (the "server" the website talks to).

It exposes a small set of web addresses (called "endpoints"):

  GET  /api/health          -> quick check that the server is running
  GET  /api/schemes         -> list of all schemes (short form, for navigation)
  GET  /api/schemes/{id}    -> full details of one scheme
  POST /api/chat            -> ask the chatbot a question (RAG)

The Streamlit website (frontend) sends requests to these endpoints and shows
the results to the farmer.
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import rag   # our RAG engine from rag.py

# ---------------------------------------------------------------------------
# Load scheme data once when the server starts
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMES_FILE = os.path.join(HERE, "..", "data", "schemes.json")

with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
    SCHEMES = json.load(f)

# A quick lookup dictionary: scheme id -> full scheme
SCHEMES_BY_ID = {s["id"]: s for s in SCHEMES}

# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TN Agriculture Welfare Schemes API",
    description="Backend for the Tamil Nadu farmers' welfare scheme portal.",
    version="1.0.0",
)

# CORS lets the Streamlit frontend (running on a different port) call this API.
# For a real deployment, replace ["*"] with your actual website address.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# The shape of the data the /api/chat endpoint expects
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    """One earlier turn in the conversation."""
    role: str             # "user" (the farmer) or "assistant" (the bot)
    content: str


class ChatRequest(BaseModel):
    question: str
    lang: str = "ta"      # "ta" = Tamil (default), "en" = English
    # The earlier conversation, so the chatbot has MEMORY of what was said.
    # It is optional — the first question simply sends an empty list.
    history: list[ChatMessage] = []


# ---------------------------------------------------------------------------
# ENDPOINT: health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "scheme_count": len(SCHEMES)}


# ---------------------------------------------------------------------------
# ENDPOINT: list all schemes (short form, used to build the navigation menu)
# ---------------------------------------------------------------------------
@app.get("/api/schemes")
def list_schemes():
    short = []
    for s in SCHEMES:
        short.append({
            "id": s["id"],
            "category_en": s["category_en"],
            "category_ta": s["category_ta"],
            "title_en": s["title_en"],
            "title_ta": s["title_ta"],
            "summary_en": s["summary_en"],
            "summary_ta": s["summary_ta"],
        })
    return {"schemes": short}


# ---------------------------------------------------------------------------
# ENDPOINT: full details of one scheme
# ---------------------------------------------------------------------------
@app.get("/api/schemes/{scheme_id}")
def get_scheme(scheme_id: str):
    scheme = SCHEMES_BY_ID.get(scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme


# ---------------------------------------------------------------------------
# ENDPOINT: chatbot (RAG)
# ---------------------------------------------------------------------------
@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    # Convert the history objects into plain dictionaries for the RAG engine.
    history = [{"role": m.role, "content": m.content} for m in req.history]
    result = rag.answer_question(req.question, lang=req.lang, history=history)
    return result


# ---------------------------------------------------------------------------
# Build the vector index as soon as the server starts (so the first
# farmer's question is fast instead of waiting for indexing).
# ---------------------------------------------------------------------------
@app.on_event("startup")
def warm_up():
    rag.get_collection()


# ---------------------------------------------------------------------------
# SERVE THE WEBSITE (frontend)
# ---------------------------------------------------------------------------
# The HTML/CSS/JS website lives in the ../web folder. We serve its files at
# /static, and serve the main page (index.html) at the site root "/".
# Because the website is served from the same address as the API, the browser
# can call "/api/..." directly with no CORS or separate port needed.
#
# NOTE: these lines are placed AFTER all the /api routes above, so the API
# always takes priority; only non-API paths fall through to the website.
WEB_DIR = os.path.join(HERE, "..", "web")

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def home_page():
    """Serve the main website page."""
    return FileResponse(os.path.join(WEB_DIR, "index.html"))
