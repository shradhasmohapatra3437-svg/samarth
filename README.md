# 🏭 SAMARTH — Smart Asset Management & Root-cause Tracking Hub

> **AI-powered Industrial Operations Intelligence Platform**  
> Built for the hackathon · React + FastAPI + ChromaDB + Groq LLM + NetworkX

---

## 📌 What is SAMARTH?

SAMARTH is an end-to-end intelligent platform for industrial asset management. It combines **Retrieval-Augmented Generation (RAG)**, **Knowledge Graphs**, **Root Cause Analysis (RCA)**, and **Compliance Auditing** into a single unified dashboard — powered by Groq LLM and vector search.

### 🔑 Key Features

| Feature | Description |
|---|---|
| 🔍 **Semantic Search** | Ask questions about equipment in plain English — answers backed by OEM manuals & regulatory docs |
| 🧠 **Root Cause Analysis** | AI-generated failure narratives with sensor context for any equipment ID |
| ✅ **Compliance Auditing** | Automated regulatory check against parsed PDF corpus with evidence packaging |
| 🕸️ **Knowledge Graph** | Interactive plant-level equipment relationship map using NetworkX |
| 🚨 **Fleet Health Intelligence** | Fleet-wide failure intelligence summaries with priority scoring |

---

## 🗂️ Project Structure

```
samarth/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # API entry point
│   ├── agent/                # LLM agent orchestration
│   ├── rag/                  # Vector search & embeddings (ChromaDB)
│   ├── rca/                  # Root cause analysis engine
│   ├── compliance/           # Regulatory compliance checker
│   ├── knowledge_graph/      # NetworkX graph builder
│   ├── ingestion/            # PDF & document ingestion pipeline
│   ├── models/               # Pydantic data models
│   ├── core/                 # Auth, DB, config
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment variable template
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   └── App.jsx           # Main dashboard component
│   ├── index.html
│   └── package.json
├── data/                     # Regulatory PDFs and OEM manuals
└── README.md
```

---

## ⚙️ Prerequisites

Make sure the following are installed on your machine:

- **Python 3.12+** → [python.org](https://www.python.org/downloads/)
- **Node.js 18+** → [nodejs.org](https://nodejs.org/)
- **Git** → [git-scm.com](https://git-scm.com/)
- **Tesseract OCR** (for PDF parsing) → [tesseract download](https://github.com/UB-Mannheim/tesseract/wiki)

---

## 🚀 First-Time Setup

> Do this **only once** when setting up the project for the first time.

### Step 1 — Clone the Repository

```powershell
git clone https://github.com/shradhasmohapatra3437-svg/samarth.git
Set-Location samarth
```

### Step 2 — Backend Setup

```powershell
# Navigate to backend
Set-Location "C:\Users\HP\OneDrive\Desktop\samarth\backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& ".\venv\Scripts\Activate.ps1"

# Install all dependencies
pip install -r requirements.txt
```

### Step 3 — Configure Environment Variables

```powershell
# Copy the example env file
Copy-Item .env.example .env
```

Then open `.env` and fill in your actual API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=samarth_secret_key_2026
DATABASE_URL=sqlite:///./samarth.db
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Step 4 — Frontend Setup

Open a **second PowerShell window** and run:

```powershell
Set-Location "C:\Users\HP\OneDrive\Desktop\samarth\frontend"
npm install
```

---

## 🔁 Daily Startup (Every Time You Open Your Laptop)

> No reinstalling needed. Just activate and run.

### 🖥️ Window 1 — Start Backend

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "C:\Users\HP\OneDrive\Desktop\samarth\backend\venv\Scripts\Activate.ps1"
Set-Location "C:\Users\HP\OneDrive\Desktop\samarth\backend"
uvicorn main:app --reload
```

✅ Backend will be live at: **http://127.0.0.1:8000**

### 🌐 Window 2 — Start Frontend

```powershell
Set-Location "C:\Users\HP\OneDrive\Desktop\samarth\frontend"
npm run dev
```

✅ Frontend will be live at: **http://localhost:5173**

---

## 🌍 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/api/query` | Semantic search over equipment corpus |
| `POST` | `/api/rca` | Root cause analysis for an equipment ID |
| `POST` | `/api/compliance` | Regulatory compliance audit |
| `GET` | `/api/graph` | Knowledge graph data |
| `GET` | `/api/fleet` | Fleet-wide health intelligence |

Interactive API docs available at: **http://127.0.0.1:8000/docs**

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | FastAPI, Python 3.12, Uvicorn |
| **LLM** | Groq (LLaMA 3), Google Generative AI |
| **Vector DB** | ChromaDB |
| **Graph Engine** | NetworkX |
| **Document Parsing** | PyMuPDF, Tesseract OCR, Transformers |
| **Auth** | JWT (python-jose, passlib) |
| **Database** | SQLite (via SQLAlchemy) |

---

## 📄 License

This project was built for hackathon purposes. All rights reserved © 2026 SAMARTH Team.
