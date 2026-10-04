# 🤖 CrewAI Multi-Agent Conversational RAG System

A multi-agent conversational AI application built with **CrewAI**, equipped with retrieval-augmented generation (RAG) over local documents and multi-turn session memory.

---

## 🏛️ Architecture

```
                               ┌─────────────────────────────┐
                               │       User Interface        │
                               │   (Terminal CLI / Web UI)   │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  CrewAI Orchestrator (Crew) │
                               │     Conversation Memory     │
                               └──────────────┬──────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Knowledge Retriever     │      │ Aggregator Host         │      │ Conversational          │
│ Specialist              │      │ Specialist              │      │ Synthesizer             │
│ - Scans documents       │─Raw─▶│ - Aggregates findings   │─Ref─▶│ - Grounded response     │
│ - Extracts excerpts     │      │ - Cross-references data │      │ - Multi-turn coherence  │
│ - Exact citations       │      │ - Host diagnostics     │      │ - Source citations      │
└────────────┬────────────┘      └────────────┬────────────┘      └────────────┬────────────┘
             │                                │                                │
             ▼                                ▼                                ▼
     ┌───────────────┐               ┌─────────────────┐               ┌────────────────┐
     │Knowledge Base │               │ Host Telemetry  │               │ Grounded Reply │
     │(Docs & FAQs)  │               │& Windows Status │               │ with Citations │
     └───────────────┘               └─────────────────┘               └────────────────┘
```


---

## 🚀 Quick Start

### 1. Configure Your API Key
Open `.env` in the project directory and insert your **Google Gemini API Key** (or OpenAI API key):
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
MODEL=gemini/gemini-1.5-flash
```
> **Get a free Gemini API key:** [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Run the Interactive Terminal CLI
To chat in your terminal with colored panels and real-time status:
```powershell
.\.venv\Scripts\python.exe main.py
```
**CLI Commands:**
- `/docs` - List all indexed documents in the knowledge base
- `/clear` - Reset conversational memory
- `/status` - Inspect active model and memory turn count
- `/exit` - Exit the chat session

### 3. Run the Modern Web Dashboard & REST API
Launch the web chat interface and modular FastAPI backend:
```powershell
.\.venv\Scripts\python.exe web_app.py
```
- **Host Network UI:** [http://10.226.157.87:8000/](http://10.226.157.87:8000/) (or `http://crewairag.com/`)
- **Interactive Swagger Docs:** [http://10.226.157.87:8000/docs](http://10.226.157.87:8000/docs)
- **ReDoc API Reference:** [http://10.226.157.87:8000/redoc](http://10.226.157.87:8000/redoc)

### 4. Run Automated API Tests
You can run tests using pytest or direct execution:
```powershell
# Run with pytest (recommended)
.\.venv\Scripts\python.exe -m pytest

# Or directly run the test file
.\.venv\Scripts\python.exe tests/test_api.py
```

---

## 📁 Knowledge Base Management
Place any markdown (`.md`), text (`.txt`), or JSON (`.json`) files into the `knowledge/` directory:
- `knowledge/company_handbook.md` (Included sample)
- `knowledge/product_manual.md` (Included sample)
- `knowledge/faq.md` (Included sample)

You can also upload documents directly through the Web UI or via the `POST /api/upload` endpoint!

---

## 🛠️ Project Structure
```
crewai_conversational_rag/
├── api/                     # Modular FastAPI Application Package
│   ├── __init__.py          # create_app() factory & app instance
│   ├── config.py            # Settings (CORS, paths, limits)
│   ├── dependencies.py      # Dependency injection providers
│   ├── routers/             # Dedicated route handlers
│   │   ├── chat.py          # /api/chat, /api/clear, /api/chat/history
│   │   ├── documents.py     # /api/documents, /api/upload, /api/documents/{name}
│   │   ├── system.py        # /api/health, /api/status
│   │   └── ui.py            # / serving the web interface
│   ├── schemas/             # Pydantic validation schemas
│   │   ├── chat.py
│   │   ├── document.py
│   │   └── system.py
│   └── services/            # Core business logic layer
│       ├── crew_service.py  # Session-isolated CrewAI manager
│       └── document_service.py # Knowledge file operations & traversal guards
├── knowledge/               # Document store (MD, TXT, JSON, etc.)
├── templates/
│   └── index.html           # Modern dark-mode web chat interface
├── tests/
│   └── test_api.py          # Automated API test suite
├── agents.py                # Specialized agent definitions (Retriever + Aggregator + Synthesizer)
├── tasks.py                 # Retrieval, aggregation & synthesis task logic
├── tools.py                 # Knowledge search & retrieval tool implementations
├── crew.py                  # Crew orchestrator & session memory
├── main.py                  # Interactive CLI interface
├── web_app.py               # FastAPI server launcher
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
└── .env                     # Local API keys and model configuration
```

