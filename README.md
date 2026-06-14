![Multimodal RAG](https://img.shields.io/badge/Multimodal-RAG-blue)
![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-red)
![Python](https://img.shields.io/badge/Python-3.13-yellow)

# Multimodal Agentic RAG System
### Enterprise Document Intelligence | Tata Steel SNTI Internship

## 🔗 Live Demo
[https://multimodal-agentic-rag.streamlit.app/](https://multimodal-agentic-rag.streamlit.app/)

## 📌 Overview
A Multimodal Retrieval-Augmented Generation (RAG) system that reads enterprise documents including PDFs, PowerPoint presentations, and Word documents — extracting and understanding both text and images (flowcharts, architecture diagrams, handwritten notes) — and answers natural language queries about their content.

## 🚀 Features
- 📄 Supports PDF, PPTX and DOCX formats
- 🖼️ Understands images, flowcharts and diagrams using Gemini Vision
- 🔍 Semantic search using Pinecone Vector Database
- 🤖 Powered by Google Gemini 3.5 Flash
- 💬 Natural language question answering
- 📦 Batch processing for multiple documents
- 🌐 Deployed on Streamlit Cloud

## 🛠️ Tech Stack
| Tool | Purpose |
|------|---------|
| Google Gemini 3.5 Flash | Vision + Text understanding |
| Gemini Embedding 001 | Text embeddings (768 dimensions) |
| Pinecone | Cloud vector database |
| ChromaDB | Local vector database |
| PyMuPDF | PDF text and image extraction |
| python-pptx | PowerPoint extraction |
| python-docx | Word document extraction |
| Streamlit | Web UI and deployment |
| Google ADK | Agent framework |

## ⚙️ How It Works
Document Upload (PDF/PPTX/DOCX)
↓
Extract Text + Images
↓
Gemini Vision describes images/flowcharts
↓
Text chunking + Embedding generation
↓
Store in Pinecone Vector Database
↓
User Query → Semantic Search → Gemini answers

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
Create a `.env` file:
GOOGLE_API_KEY=your_gemini_api_key

PINECONE_API_KEY=your_pinecone_api_key

### 4. Run the app
```bash
streamlit run app.py
```

## 📖 Usage
1. Upload your PDF, PPTX or DOCX files
2. Click **Ingest** to process documents
3. Go to **Ask Questions** tab
4. Type your question and click **Search**

## 🏢 Project Context
Built as part of the **Enterprise Intelligence Layer** project at **Tata Steel SNTI, Jamshedpur** — an agentic RAG system designed to enable intelligent document understanding across cross-domain knowledge bases for senior leadership.

## 👩‍💻 Author
**Prajakta Kuila**  
AI Intern — Tata Steel SNTI  
May 2026 – Jun 2026