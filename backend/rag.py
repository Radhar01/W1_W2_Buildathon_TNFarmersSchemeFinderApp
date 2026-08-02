"""
rag.py  -  The Retrieval-Augmented Generation (RAG) engine.

What this file does, step by step:
  1. Loads the schemes from data/schemes.json
  2. Turns each scheme into a text "document" and stores its embedding
     (a numeric fingerprint of the meaning) inside a local ChromaDB database.
  3. When a farmer asks a question, it finds the most relevant schemes
     and asks an LLM (Large Language Model) to answer using ONLY those schemes.
  4. The answer is returned in the language the user selected (Tamil or English).

Everything is heavily commented so it is easy to follow.
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI            # used to talk to the Groq / OpenAI-compatible API
from dotenv import load_dotenv

# Load the values from the .env file (API keys etc.) into the environment
load_dotenv()

# ---------------------------------------------------------------------------
# 1. FILE PATHS
# ---------------------------------------------------------------------------
# Folder where this file lives
HERE = os.path.dirname(os.path.abspath(__file__))
# Path to the scheme data (one folder up, inside /data)
SCHEMES_FILE = os.path.join(HERE, "..", "data", "schemes.json")
# Folder where ChromaDB will keep the vector database on disk
CHROMA_DIR = os.path.join(HERE, "chroma_store")

# ---------------------------------------------------------------------------
# 2. EMBEDDING MODEL  (multilingual so it understands Tamil AND English)
# ---------------------------------------------------------------------------
# This small model runs locally. The first run downloads it once.
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)

# ---------------------------------------------------------------------------
# 3. LLM (chat model) CONFIGURATION
# ---------------------------------------------------------------------------
# We use an OpenAI-compatible client. By default it points to Groq, which is
# fast and has a generous free tier. You can switch to OpenAI or Ollama by
# changing LLM_BASE_URL, LLM_API_KEY and LLM_MODEL in the .env file.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Create the client (only if a key is present)
llm_client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY) if LLM_API_KEY else None


# ---------------------------------------------------------------------------
# 4. LOAD THE SCHEMES FROM DISK
# ---------------------------------------------------------------------------
def load_schemes():
    """Read schemes.json and return it as a Python list."""
    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def scheme_to_text(scheme):
    """
    Flatten one scheme dictionary into a single searchable text block.
    We include both English and Tamil so the search works in either language.
    """
    parts = [
        scheme["title_en"], scheme["title_ta"],
        scheme["category_en"], scheme["category_ta"],
        scheme["summary_en"], scheme["summary_ta"],
        "Benefits: " + " ".join(scheme["benefits_en"]),
        "நன்மைகள்: " + " ".join(scheme["benefits_ta"]),
        "Eligibility: " + " ".join(scheme["eligibility_en"]),
        "தகுதி: " + " ".join(scheme["eligibility_ta"]),
        "Districts: " + scheme.get("districts_en", ""),
        "Officers: " + " ".join(scheme["officers_en"]),
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 5. BUILD (or open) THE VECTOR DATABASE
# ---------------------------------------------------------------------------
# We keep a single global collection so we build it only once per server run.
_collection = None


def get_collection():
    """
    Return the ChromaDB collection, building it the first time it is called.
    ChromaDB persists to disk, so on later runs it just re-opens the store.
    """
    global _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # get_or_create means: reuse the collection if it already exists
    collection = client.get_or_create_collection(
        name="schemes",
        embedding_function=embedding_fn,
    )

    # If the collection is empty, fill it with our scheme documents
    if collection.count() == 0:
        schemes = load_schemes()
        documents = [scheme_to_text(s) for s in schemes]
        ids = [s["id"] for s in schemes]
        metadatas = [
            {"title_en": s["title_en"], "title_ta": s["title_ta"], "id": s["id"]}
            for s in schemes
        ]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"[rag] Indexed {len(schemes)} schemes into ChromaDB.")
    else:
        print(f"[rag] Re-using existing index with {collection.count()} schemes.")

    _collection = collection
    return _collection


# ---------------------------------------------------------------------------
# 6. RETRIEVE THE MOST RELEVANT SCHEMES FOR A QUESTION
# ---------------------------------------------------------------------------
def retrieve(question, top_k=4):
    """
    Find the top_k schemes whose meaning is closest to the question.
    Returns a list of matching scheme ids and their text.
    """
    collection = get_collection()
    results = collection.query(query_texts=[question], n_results=top_k)

    # ChromaDB returns nested lists; unwrap the first (and only) query result
    docs = results["documents"][0]
    ids = results["ids"][0]
    return list(zip(ids, docs))


# ---------------------------------------------------------------------------
# 7. ASK THE LLM  (this is the "Generation" in RAG)
# ---------------------------------------------------------------------------
# How many past messages (user + bot together) to remember at most.
# We keep this small so the conversation stays fast and within token limits.
MAX_HISTORY_MESSAGES = 10


def answer_question(question, lang="ta", history=None, top_k=4):
    """
    Main entry point used by the FastAPI backend.
      question : the farmer's question (any language)
      lang     : "ta" for Tamil answer, "en" for English answer
      history  : the earlier conversation, so the bot has MEMORY. It is a list
                 of {"role": "user"/"assistant", "content": "..."} dictionaries.
                 Pass None or [] for the very first question.
    Returns a dict: {"answer": ..., "sources": [scheme ids used]}
    """
    # If no history was given, start with an empty list.
    history = history or []

    # -- Use memory to improve retrieval for follow-up questions --
    # A follow-up like "what about its eligibility?" has no scheme name in it.
    # By adding the last couple of user messages to the search query, we still
    # find the scheme the farmer was already talking about.
    recent_user_turns = [
        m["content"] for m in history
        if m.get("role") == "user" and m.get("content")
    ][-2:]
    retrieval_query = " ".join(recent_user_turns + [question])

    matches = retrieve(retrieval_query, top_k=top_k)
    context = "\n\n---\n\n".join(doc for _id, doc in matches)
    source_ids = [_id for _id, _doc in matches]

    # Decide the language for the reply
    language_name = "Tamil" if lang == "ta" else "English"

    # If no LLM key is set, fall back to simply returning the retrieved context.
    # This lets the app run for testing even without an API key.
    if llm_client is None:
        fallback = (
            "(LLM key not configured — showing the most relevant scheme details.)\n\n"
            + context
        )
        return {"answer": fallback, "sources": source_ids}

    # The system prompt tells the model how to behave.
    system_prompt = (
        "You are a helpful assistant for the Tamil Nadu Department of Agriculture. "
        "You answer farmers' questions about government welfare schemes. "
        f"Always reply in {language_name}. "
        "Use ONLY the scheme information provided in the context. "
        "You may use the earlier conversation to understand follow-up questions "
        "(for example, when the farmer says 'it' or 'that scheme'), but never "
        "invent scheme details that are not in the context. "
        "If the context does not contain the answer, say politely that the "
        "information is not available and suggest contacting the local "
        "Agricultural Officer. Be clear, simple and respectful. "
        "When useful, mention the benefit amounts, eligibility and which officer to contact."
    )

    user_prompt = (
        f"Scheme context:\n{context}\n\n"
        f"Farmer's question: {question}\n\n"
        f"Answer in {language_name}:"
    )

    # -- Build the message list the model will see --
    # 1) the system instructions
    # 2) the recent conversation history (this is the MEMORY)
    # 3) the current question, wrapped with the freshly retrieved scheme context
    messages = [{"role": "system", "content": system_prompt}]

    for m in history[-MAX_HISTORY_MESSAGES:]:
        role = m.get("role")
        content = m.get("content")
        # Only pass clean user/assistant turns to the model.
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_prompt})

    # Call the chat model
    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,   # low temperature = factual, less creative
    )

    answer_text = response.choices[0].message.content
    return {"answer": answer_text, "sources": source_ids}


# ---------------------------------------------------------------------------
# 8. QUICK SELF-TEST  (run:  python rag.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    get_collection()  # build the index

    # First question
    demo = answer_question("What subsidy is available for drip irrigation?", lang="en")
    print("\nANSWER 1:\n", demo["answer"])
    print("\nSOURCES:", demo["sources"])

    # Follow-up question that relies on MEMORY ("it" = the scheme above).
    history = [
        {"role": "user", "content": "What subsidy is available for drip irrigation?"},
        {"role": "assistant", "content": demo["answer"]},
    ]
    demo2 = answer_question("Who is eligible for it?", lang="en", history=history)
    print("\nANSWER 2 (follow-up):\n", demo2["answer"])
    print("\nSOURCES:", demo2["sources"])
