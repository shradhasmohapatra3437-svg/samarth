import os
from dotenv import load_dotenv

# Force Hugging Face and Transformers to offline mode to prevent DNS lookup crashes on offline networks
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "samarth_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./samarth.db")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
REGULATORY_DIR = os.path.join(DATA_DIR, "regulatory")
GENERATED_DIR = os.path.join(DATA_DIR, "generated")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

# ChromaDB
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")

# Tesseract
TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Chunking settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# LLM Models
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MODEL_FAST = "llama-3.3-70b-versatile"

# Regulatory body mapping
REGULATORY_BODIES = {
    "oisd": "Oil Industry Safety Directorate",
    "factories_act": "Ministry of Labour and Employment",
    "dgms": "Directorate General of Mines Safety",
    "peso": "Petroleum and Explosives Safety Organisation"
}
