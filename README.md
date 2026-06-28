![Multimodal RAG](https://img.shields.io/badge/Multimodal-RAG-blue)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange)
![Google ADK](https://img.shields.io/badge/Google%20ADK-MoE%20Agents-purple)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-red)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)

# Multimodal Agentic RAG — Mixture of Experts
### Enterprise Document Intelligence | Tata Steel SNTI Internship

## 🔗 Live Demo
[https://multimodal-agentic-rag.streamlit.app/](https://multimodal-agentic-rag.streamlit.app/)

---

## 📌 Overview

A **Multimodal Agentic RAG system** built with a **Mixture of Experts (MoE)** architecture that reads enterprise documents — PDFs, PowerPoint presentations, and Word documents — extracting and understanding both text and embedded visuals (flowcharts, architecture diagrams, schematics). A **Router/Orchestrator Agent** powered by Google ADK classifies each incoming query and delegates it to one of three domain-specialised sub-agents, each performing metadata-filtered retrieval from a Pinecone vector database.

Built as part of the **Enterprise Intelligence Layer** project at **Tata Steel SNTI, Jamshedpur**.

---

## 🚀 Features

- **Multimodal ingestion** — PDF, PPTX, and DOCX with text and image extraction
- **Gemini Vision** — auto-generates semantic descriptions for diagrams, flowcharts, and figures
- **Mixture of Experts (MoE)** — Router agent delegates to specialised sub-agents based on query type
- **Metadata-filtered retrieval** — each expert searches only its content type (text vs image chunks)
- **Multi-turn conversation memory** — follow-up questions retain context via ADK `InMemorySessionService`
- **Real-time streaming** — answers stream word by word like a native LLM interface
- **Expert attribution** — every answer shows which expert (🔵 Text / 🟢 Visual / 🟡 Synthesis) responded
- **Persistent vector store** — all ingested documents survive app restarts via Pinecone Cloud
- **Deployed on Streamlit Cloud**

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Google Gemini 2.5 Flash | Generation model for all agents |
| Gemini Vision | Image and diagram understanding |
| `gemini-embedding-001` | Text embeddings — 768 dimensions |
| Google ADK | Agent framework — Router + 3 expert sub-agents |
| Pinecone | Cloud vector database with metadata filtering |
| PyMuPDF | PDF text and image extraction |
| python-pptx | PowerPoint text and image extraction |
| python-docx | Word document text and image extraction |
| Streamlit | Chat UI and cloud deployment |

---

## 🏗️ Architecture — Mixture of Experts Pipeline

```
          User Query
              │
              ▼
┌─────────────────────────────┐
│   Router / Orchestrator     │  ← Google ADK Agent
│   Classifies query type     │
└────────────┬────────────────┘
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
 ┌───────┐ ┌──────┐ ┌──────────┐
 │ Text  │ │Visual│ │Synthesis │  ← Specialist Sub-Agents
 │Expert │ │Expert│ │ Expert   │
 └───┬───┘ └──┬───┘ └────┬─────┘
     │        │           │
     ▼        ▼           ▼
 text only  image only  all chunks
 (filtered) (filtered)  (top-10)
     │        │           │
     └────────┴─────┬─────┘
                    ▼
             Pinecone Vector DB
                    │
                    ▼
         Streamed Answer + Source Citations
```

### Expert Routing Logic

| Query type | Routed to |
|---|---|
| Written content — policies, procedures, specs | 🔵 Text Expert |
| Diagrams, flowcharts, figures, schematics | 🟢 Visual Expert |
| Cross-document comparison, broad summaries | 🟡 Synthesis Expert |
| "What documents are available?" | `list_ingested_documents` tool |

---

## ⚙️ Ingestion Pipeline

```
Upload PDF / PPTX / DOCX
        │
        ├── Extract text chunks (500 words, 50-word overlap)
        │
        └── Extract embedded images
                │
                └── Gemini Vision generates semantic description
                        │
                        ▼
             gemini-embedding-001 (768-dim embeddings)
                        │
                        ▼
              Pinecone — stored with metadata:
              { source, page, type: "text"|"image", content }
```

---

## 🔧 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/prajakta-k19/multimodal-agentic-rag.git
cd multimodal-agentic-rag
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_ai_studio_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

> Get your Google API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)  
> Get your Pinecone API key from [pinecone.io](https://pinecone.io)  
> Create a Pinecone index named `multimodal-rag` with **768 dimensions** and **cosine** metric

### 4. Run the app
```bash
python -m streamlit run app.py
```

---

## 💬 Usage

1. **Upload documents** — use the sidebar to upload one or more PDF, PPTX, or DOCX files
2. **Ingest** — click *Ingest Documents*; the pipeline extracts text and images, generates embeddings, and stores them in Pinecone. The chat resets automatically after ingestion.
3. **Ask questions** — type in the chat box; the Router classifies your query and delegates to the right expert
4. **Follow-up freely** — the system maintains conversation context so you can ask follow-up questions without repeating yourself
5. **Check the badge** — each answer shows which expert responded (🔵 Text / 🟢 Visual / 🟡 Synthesis)

---

## 📁 Project Structure

```
multimodal-agentic-rag/
├── agent.py          # Ingestion pipeline + MoE agents (ADK)
├── app.py            # Streamlit chat UI with streaming
├── requirements.txt
├── .env              # API keys (not committed)
├── .gitignore
├── sample.pdf        # Sample enterprise document
└── sample.pptx       # Sample presentation
```

---

## 🏢 Project Context

Built as part of the **Enterprise Intelligence Layer** project at **Tata Steel SNTI, Jamshedpur** — an agentic RAG system designed to enable intelligent document understanding across cross-domain knowledge bases for senior leadership.

**Internship period:** May 2026 – June 2026

---

## 👩‍💻 Author

**Prajakta Kuila**  
AI Intern — Tata Steel SNTI  
[github.com/prajakta-k19](https://github.com/prajakta-k19)
