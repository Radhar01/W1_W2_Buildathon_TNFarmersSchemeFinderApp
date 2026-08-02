# TN Agriculture Welfare Schemes Portal 🌾

A bilingual (Tamil + English) web portal that helps farmers in Tamil Nadu
search and understand agriculture welfare schemes — their benefits, eligibility
and which officer to contact. It includes a **RAG chatbot** so farmers can ask
questions in plain Tamil or English.

- **Backend:** FastAPI (also serves the website)
- **Frontend:** A government-styled HTML/CSS/JS website — hero header with Tamil
  Nadu farmer photos, scheme cards with thumbnails on the home page, a scheme
  detail page with a searchable left navigation (the selected scheme is
  highlighted), and a floating chat button on every page. Opens in Tamil by
  default, with an English toggle.
- **AI:** Retrieval-Augmented Generation (RAG) using ChromaDB + a multilingual
  embedding model + an LLM (Groq / OpenAI / Ollama — configurable). The chatbot
  has **memory** of the conversation.
- **Data:** The scheme content extracted from the department PDF into
  `data/schemes.json`

> There are **two** frontends, and both now use the same design (farmer-photo
> header, scheme cards with thumbnails, a detail page with a searchable left
> menu that highlights the selected scheme, and a help chatbot with memory):
>
> - **`web/`** — plain HTML/CSS/JS, served by FastAPI. Run one server, open
>   http://localhost:8000/. The chat is a floating bottom-right widget.
> - **`frontend/`** — a **pure Streamlit** version (run with `streamlit run
>   app.py`). The chat lives in the side panel (Streamlit can't float a widget).
>   Use this one if your assignment requires Streamlit.
>
> Both talk to the same backend and API.

---

## Project structure

```
tn-agri-schemes/
├── data/
│   └── schemes.json          # All scheme content (Tamil + English)
├── backend/
│   ├── main.py               # FastAPI app (API endpoints)
│   └── rag.py                # RAG engine (embeddings + retrieval + LLM)
├── web/                     # NEW recommended frontend (served by FastAPI)
│   ├── index.html           # Page shell (home + detail + chat)
│   ├── styles.css           # Government-style theme
│   └── app.js               # Data fetching, language toggle, chat memory
├── frontend/                # Older Streamlit frontend (optional alternative)
│   ├── app.py               # Streamlit website
│   └── translations.py      # All UI labels in Tamil + English
├── requirements.txt
├── .env.example              # Copy to .env and add your API key
└── README.md
```

---

## How it works (in plain words)

1. On startup, the backend reads `schemes.json`, converts each scheme into a
   text block, and stores a numeric "meaning fingerprint" (embedding) of it in a
   local ChromaDB database.
2. The Streamlit site shows the schemes grouped by category. Categories are
   **collapsed by default**; clicking a scheme name opens its full details.
3. When a farmer types a question in the chatbot, the backend finds the most
   relevant schemes and asks the LLM to answer **using only those schemes**, in
   the language the farmer selected.

---

## Setup — step by step

### 1. Create a virtual environment and install packages

```bash
cd tn-agri-schemes
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Add your LLM key

```bash
# copy the example file
cp .env.example .env        # Windows: copy .env.example .env
```

Open `.env` and paste your Groq API key (free at https://console.groq.com).
You can also switch to OpenAI or a local Ollama model — see the comments in the file.

> The app still runs **without** a key: the chatbot will simply return the most
> relevant scheme text instead of a generated answer. This is handy for testing.

### 3. Start the server (just one!)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The first run downloads the embedding model and builds the index (this takes a
minute). Leave this terminal running.

### 4. Open the website

Open **http://localhost:8000/** in your browser.

That's it — the same server hosts both the website and the API. The portal opens
in Tamil; use the **தமிழ் / English** switch at the top right to change language.
Click a scheme card to open its detail page (with the searchable left menu), and
use the **💬 chat button** at the bottom-right on any page to ask questions.

> **Testing just the backend?** Open http://localhost:8000/api/health for a
> quick check, or http://localhost:8000/docs for the interactive API page.

### (Optional) Run the Streamlit version instead

The Streamlit frontend uses the **same redesign** (photo header, scheme cards,
searchable highlighted left menu, side-panel chat with memory). Start the
backend first (Step 3 above), then in a second terminal:

```bash
cd frontend
streamlit run app.py     # opens on http://localhost:8501
```

The backend must be running because Streamlit calls the same API for scheme
data and chat answers.

---

## API endpoints (backend)

| Method | Endpoint              | Purpose                                  |
|--------|-----------------------|------------------------------------------|
| GET    | `/api/health`         | Check the server is running              |
| GET    | `/api/schemes`        | List all schemes (for the menu)          |
| GET    | `/api/schemes/{id}`   | Full details of one scheme               |
| POST   | `/api/chat`           | Ask the RAG chatbot (`{question, lang, history}`) |

Interactive API docs are auto-generated at http://localhost:8000/docs

---

## Important notes for a government deployment

- **Verify the Tamil content.** The Tamil text in `schemes.json` was translated
  for this prototype. Before going live on a real government site, have the
  department verify all Tamil scheme text against official translations.
- **Restrict CORS.** In `backend/main.py`, replace `allow_origins=["*"]` with
  your real website domain.
- **Add more schemes** by appending entries to `data/schemes.json` (follow the
  same fields). Delete the `backend/chroma_store/` folder once after editing so
  the index rebuilds with the new content.
- **Frontend photos.** The header and card photos load from Wikimedia Commons
  (freely licensed) via hotlink, so the site needs internet access to show them.
  For an offline/production deploy, download the images into `web/images/` and
  point the URLs in `web/app.js` at those local files. If any photo fails to
  load, the design falls back to a coloured tile with an icon automatically.
- **Two frontends.** The recommended `web/` site is plain HTML/CSS/JS served by
  FastAPI — easy to restyle to exact government branding. The older Streamlit
  app in `frontend/` remains as an alternative; both use the same API.
